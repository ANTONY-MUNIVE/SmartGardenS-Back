"""
Pruebas unitarias del dominio puro.
Sin base de datos, sin servidor, sin MQTT.
Cobertura objetivo: 85% — ejecutables en < 3 segundos.
"""

from datetime import datetime

import pytest

from domain.entities.sensor_reading import (
    Alerta,
    Experimento,
    LecturaSensor,
)
from infrastructure.adapters.output.motor_ia import MotorReglas


@pytest.fixture
def lectura_optima():
    return LecturaSensor(
        temperatura=22.0,
        humedad_suelo=55.0,
        humedad_ambiental=60.0,
        luminosidad=800.0,
    )


@pytest.fixture
def lectura_critica():
    return LecturaSensor(
        temperatura=35.0,
        humedad_suelo=15.0,
        humedad_ambiental=30.0,
        luminosidad=100.0,
    )


@pytest.fixture
def motor():
    return MotorReglas()


class TestLecturaSensor:
    def test_lectura_valida(self, lectura_optima):
        assert lectura_optima.es_valida() is True

    def test_temperatura_fuera_de_rango(self):
        lectura = LecturaSensor(
            temperatura=70.0,
            humedad_suelo=50,
            humedad_ambiental=50,
            luminosidad=500,
        )
        assert lectura.es_valida() is False

    def test_humedad_negativa_invalida(self):
        lectura = LecturaSensor(
            temperatura=25.0,
            humedad_suelo=-5,
            humedad_ambiental=50,
            luminosidad=500,
        )
        assert lectura.es_valida() is False

    def test_timestamp_generado_automaticamente(self):
        lectura = LecturaSensor(
            temperatura=20,
            humedad_suelo=50,
            humedad_ambiental=50,
            luminosidad=500,
        )
        assert isinstance(lectura.timestamp, datetime)


class TestMotorReglas:
    def test_estado_optimo_sin_alertas(self, motor, lectura_optima):
        recs = motor.analizar(lectura_optima)
        assert len(recs) == 1
        assert recs[0].accion == "estado_optimo"
        assert recs[0].confianza == 0.99

    def test_riego_urgente_humedad_baja(self, motor):
        lectura = LecturaSensor(
            temperatura=25.0,
            humedad_suelo=20.0,
            humedad_ambiental=50,
            luminosidad=500,
        )
        recs = motor.analizar(lectura)
        acciones = [r.accion for r in recs]
        assert "riego_urgente" in acciones

    def test_riego_urgente_100_porciento_en_escenario_critico(
        self,
        motor,
        lectura_critica,
    ):
        recs = motor.analizar(lectura_critica)
        riego = next(r for r in recs if r.accion == "riego_urgente")
        assert riego is not None
        assert riego.confianza >= 0.95

    def test_temperatura_alta_genera_alerta(self, motor):
        lectura = LecturaSensor(
            temperatura=35.0,
            humedad_suelo=50,
            humedad_ambiental=50,
            luminosidad=500,
        )
        recs = motor.analizar(lectura)
        assert any(r.accion == "alerta_temperatura" for r in recs)

    def test_luz_baja_bajo_umbral_fotosintesis(self, motor):
        lectura = LecturaSensor(
            temperatura=22.0,
            humedad_suelo=50,
            humedad_ambiental=50,
            luminosidad=100,
        )
        recs = motor.analizar(lectura)
        assert any(r.accion == "alerta_luz" for r in recs)

    def test_ley_fick_aumenta_confianza(self, motor):
        lectura = LecturaSensor(
            temperatura=34.0,
            humedad_suelo=20.0,
            humedad_ambiental=40,
            luminosidad=500,
        )
        recs = motor.analizar(lectura)
        riego = next(r for r in recs if r.accion == "riego_urgente")
        assert riego.confianza == 1.0

    def test_prediccion_sin_historial_devuelve_none(self, motor):
        assert motor.predecir_humedad([]) is None

    def test_prediccion_con_historial_devuelve_float(self, motor):
        historial = [
            LecturaSensor(
                temperatura=22,
                humedad_suelo=50 - i * 2,
                humedad_ambiental=55,
                luminosidad=700,
            )
            for i in range(5)
        ]

        resultado = motor.predecir_humedad(historial)

        assert isinstance(resultado, float)
        assert 0.0 <= resultado <= 100.0


class TestAlerta:
    def test_alerta_creada_con_campos_correctos(self):
        alerta = Alerta(
            tipo="riego_urgente",
            mensaje="Humedad crítica",
            prioridad="alta",
        )

        assert alerta.tipo == "riego_urgente"
        assert alerta.prioridad == "alta"
        assert isinstance(alerta.timestamp, datetime)


class TestExperimento:
    def test_experimento_creado(self):
        exp = Experimento(
            titulo="Efecto de la luz en el crecimiento",
            descripcion="Medir crecimiento en 3 condiciones de luz",
            estudiante="Ana García",
        )

        assert exp.titulo == "Efecto de la luz en el crecimiento"
        assert exp.observaciones == ""