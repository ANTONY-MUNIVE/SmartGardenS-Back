"""
Adaptador de entrada: suscriptor MQTT.
Patrón Adapter — aísla el protocolo MQTT del dominio.
El dominio solo conoce LecturaSensor; nunca conoce paho-mqtt.
"""
import asyncio
import json
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

from backend.domain.entities.sensor_reading import LecturaSensor
from backend.domain.ports.ports import SensorPublisher

logger = logging.getLogger(__name__)


class MQTTSensorAdapter:
    """
    Se suscribe al topic 'huerto/sensores' en HiveMQ.
    Cuando llega un mensaje JSON del ESP32, lo convierte en LecturaSensor
    y llama al publisher del dominio (patrón Observer).
    """

    TOPIC = "huerto/sensores"

    def __init__(
        self,
        broker_host: str,
        broker_port: int,
        publisher: SensorPublisher,
        loop: asyncio.AbstractEventLoop,
    ):
        self._publisher = publisher
        self._loop = loop

        self._client = mqtt.Client(client_id="smartgarden-backend")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.connect_async(broker_host, broker_port)

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("MQTT conectado. Suscribiendo a '%s'", self.TOPIC)
            client.subscribe(self.TOPIC)
        else:
            logger.error("MQTT error de conexión: rc=%s", rc)

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            lectura = LecturaSensor(
                temperatura=float(payload["temperatura"]),
                humedad_suelo=float(payload["humedad_suelo"]),
                humedad_ambiental=float(payload["humedad_ambiental"]),
                luminosidad=float(payload["luminosidad"]),
                timestamp=datetime.utcnow(),
            )
            asyncio.run_coroutine_threadsafe(
                self._publisher.publicar(lectura), self._loop
            )
        except (KeyError, ValueError, json.JSONDecodeError) as exc:
            logger.warning("Payload MQTT inválido: %s | Error: %s", msg.payload, exc)

    def iniciar(self):
        self._client.loop_start()
        logger.info("MQTT loop iniciado.")

    def detener(self):
        self._client.loop_stop()
        self._client.disconnect()
        logger.info("MQTT desconectado.")
