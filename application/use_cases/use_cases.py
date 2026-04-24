"""
Casos de uso — capa de aplicación.
Orquestan el dominio sin conocer frameworks ni bases de datos.
"""
from domain.entities.sensor_reading import (
    Alerta,
    Experimento,
    LecturaSensor,
    Recomendacion,
)
from domain.ports.ports import (
    AlertaRepository,
    ExperimentoRepository,
    MotorIA,
    SensorRepository,
)


class MonitorearAmbiente:
    """
    UC-01: Recibir una lectura del ESP32, validarla, persistirla
    y disparar el análisis de IA.
    """

    def __init__(
        self,
        sensor_repo: SensorRepository,
        alerta_repo: AlertaRepository,
        motor_ia: MotorIA,
    ):
        self._sensor_repo = sensor_repo
        self._alerta_repo = alerta_repo
        self._motor_ia = motor_ia

    async def ejecutar(
        self, lectura: LecturaSensor
    ) -> tuple[LecturaSensor, list[Recomendacion], list[Alerta]]:
        if not lectura.es_valida():
            raise ValueError(f"Lectura fuera de rango: {lectura}")

        lectura_guardada = await self._sensor_repo.guardar(lectura)

        recomendaciones = self._motor_ia.analizar(lectura_guardada)

        alertas: list[Alerta] = []
        for rec in recomendaciones:
            if rec.confianza >= 0.8:
                alerta = Alerta(
                    tipo=rec.accion,
                    mensaje=rec.razon,
                    prioridad="alta" if rec.confianza >= 0.95 else "media",
                    lectura_id=lectura_guardada.id,
                )
                alertas.append(await self._alerta_repo.guardar(alerta))

        return lectura_guardada, recomendaciones, alertas


class ObtenerEstadoHuerto:
    """
    UC-02: Devolver las últimas lecturas + alertas activas + predicción.
    """

    def __init__(
        self,
        sensor_repo: SensorRepository,
        alerta_repo: AlertaRepository,
        motor_ia: MotorIA,
    ):
        self._sensor_repo = sensor_repo
        self._alerta_repo = alerta_repo
        self._motor_ia = motor_ia

    async def ejecutar(self) -> dict:
        lecturas = await self._sensor_repo.obtener_ultimas(20)
        alertas = await self._alerta_repo.obtener_recientes(5)
        prediccion = self._motor_ia.predecir_humedad(lecturas)

        ultima = lecturas[0] if lecturas else None

        return {
            "ultima_lectura": ultima,
            "historial": lecturas,
            "alertas_activas": alertas,
            "prediccion_humedad": prediccion,
        }


class GestionarExperimento:
    """
    UC-03: Crear y consultar experimentos educativos STEAM.
    """

    def __init__(self, experimento_repo: ExperimentoRepository):
        self._repo = experimento_repo

    async def crear(self, experimento: Experimento) -> Experimento:
        return await self._repo.guardar(experimento)

    async def listar(self) -> list[Experimento]:
        return await self._repo.listar()

    async def obtener(self, id: int) -> Experimento | None:
        return await self._repo.obtener_por_id(id)
