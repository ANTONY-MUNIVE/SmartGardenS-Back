"""
Adaptadores de salida — repositorios PostgreSQL con SQLAlchemy.
Implementan los puertos del dominio; el dominio no los conoce directamente.
"""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String, Text, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from domain.entities.sensor_reading import (
    Alerta,
    Experimento,
    LecturaSensor,
)
from domain.ports.ports import (
    AlertaRepository,
    ExperimentoRepository,
    SensorRepository,
)


# ── Modelos ORM ───────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


class LecturaSensorORM(Base):
    __tablename__ = "lecturas_sensor"

    id = Column(Integer, primary_key=True, index=True)
    temperatura = Column(Float, nullable=False)
    humedad_suelo = Column(Float, nullable=False)
    humedad_ambiental = Column(Float, nullable=False)
    luminosidad = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class AlertaORM(Base):
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(100), nullable=False)
    mensaje = Column(Text, nullable=False)
    prioridad = Column(String(20), nullable=False)
    lectura_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)


class ExperimentoORM(Base):
    __tablename__ = "experimentos"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    estudiante = Column(String(150), nullable=False)
    fecha_inicio = Column(DateTime, default=datetime.utcnow)
    fecha_fin = Column(DateTime, nullable=True)
    observaciones = Column(Text, default="")


# ── Mapeadores dominio ↔ ORM ──────────────────────────────────────────────────

def _orm_a_lectura(orm: LecturaSensorORM) -> LecturaSensor:
    return LecturaSensor(
        id=orm.id,
        temperatura=orm.temperatura,
        humedad_suelo=orm.humedad_suelo,
        humedad_ambiental=orm.humedad_ambiental,
        luminosidad=orm.luminosidad,
        timestamp=orm.timestamp,
    )


def _orm_a_alerta(orm: AlertaORM) -> Alerta:
    return Alerta(
        id=orm.id,
        tipo=orm.tipo,
        mensaje=orm.mensaje,
        prioridad=orm.prioridad,
        lectura_id=orm.lectura_id,
        timestamp=orm.timestamp,
    )


def _orm_a_experimento(orm: ExperimentoORM) -> Experimento:
    return Experimento(
        id=orm.id,
        titulo=orm.titulo,
        descripcion=orm.descripcion,
        estudiante=orm.estudiante,
        fecha_inicio=orm.fecha_inicio,
        fecha_fin=orm.fecha_fin,
        observaciones=orm.observaciones or "",
    )


# ── Repositorios ──────────────────────────────────────────────────────────────

class SensorRepositoryPostgres(SensorRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def guardar(self, lectura: LecturaSensor) -> LecturaSensor:
        orm = LecturaSensorORM(
            temperatura=lectura.temperatura,
            humedad_suelo=lectura.humedad_suelo,
            humedad_ambiental=lectura.humedad_ambiental,
            luminosidad=lectura.luminosidad,
            timestamp=lectura.timestamp,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _orm_a_lectura(orm)

    async def obtener_ultimas(self, n: int = 20) -> list[LecturaSensor]:
        stmt = (
            select(LecturaSensorORM)
            .order_by(LecturaSensorORM.timestamp.desc())
            .limit(n)
        )
        result = await self._session.execute(stmt)
        return [_orm_a_lectura(r) for r in result.scalars()]

    async def obtener_por_rango(
        self, desde: datetime, hasta: datetime
    ) -> list[LecturaSensor]:
        stmt = (
            select(LecturaSensorORM)
            .where(
                LecturaSensorORM.timestamp >= desde,
                LecturaSensorORM.timestamp <= hasta,
            )
            .order_by(LecturaSensorORM.timestamp.asc())
        )
        result = await self._session.execute(stmt)
        return [_orm_a_lectura(r) for r in result.scalars()]


class AlertaRepositoryPostgres(AlertaRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def guardar(self, alerta: Alerta) -> Alerta:
        orm = AlertaORM(
            tipo=alerta.tipo,
            mensaje=alerta.mensaje,
            prioridad=alerta.prioridad,
            lectura_id=alerta.lectura_id,
            timestamp=alerta.timestamp,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _orm_a_alerta(orm)

    async def obtener_recientes(self, n: int = 10) -> list[Alerta]:
        stmt = (
            select(AlertaORM)
            .order_by(AlertaORM.timestamp.desc())
            .limit(n)
        )
        result = await self._session.execute(stmt)
        return [_orm_a_alerta(r) for r in result.scalars()]


class ExperimentoRepositoryPostgres(ExperimentoRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def guardar(self, experimento: Experimento) -> Experimento:
        orm = ExperimentoORM(
            titulo=experimento.titulo,
            descripcion=experimento.descripcion,
            estudiante=experimento.estudiante,
            fecha_inicio=experimento.fecha_inicio,
            fecha_fin=experimento.fecha_fin,
            observaciones=experimento.observaciones,
        )
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return _orm_a_experimento(orm)

    async def listar(self) -> list[Experimento]:
        stmt = select(ExperimentoORM).order_by(ExperimentoORM.fecha_inicio.desc())
        result = await self._session.execute(stmt)
        return [_orm_a_experimento(r) for r in result.scalars()]

    async def obtener_por_id(self, id: int) -> Experimento | None:
        stmt = select(ExperimentoORM).where(ExperimentoORM.id == id)
        result = await self._session.execute(stmt)
        orm = result.scalar_one_or_none()
        return _orm_a_experimento(orm) if orm else None


# ── Configuración de base de datos ────────────────────────────────────────────

def crear_engine(database_url: str):
    return create_async_engine(database_url, echo=False)


def crear_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def inicializar_tablas(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
