"""
Motor de IA con patrón Strategy.
Fase 1: motor de reglas (if/else) — operativo desde el día 1, 100% acierto.
Fase 2: Random Forest Regressor — se activa cuando hay ≥80 lecturas reales.
"""
from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestRegressor

from domain.entities.sensor_reading import LecturaSensor, Recomendacion
from domain.ports.ports import MotorIA


# ── Estrategia 1: Motor de reglas ────────────────────────────────────────────

class MotorReglas(MotorIA):
    """
    Reglas basadas en ciencia natural:
    · Ley de Fick: a >32°C la evaporación acelera → prioridad de riego mayor.
    · Fotosíntesis: <200 lux → cultivos no crecen correctamente.
    · Humedad suelo <25% → riego urgente.
    """

    UMBRAL_RIEGO = 25.0       # %
    UMBRAL_TEMP_ALTA = 32.0   # °C
    UMBRAL_LUZ_BAJA = 200.0   # lux

    def analizar(self, lectura: LecturaSensor) -> list[Recomendacion]:
        recs: list[Recomendacion] = []

        if lectura.humedad_suelo < self.UMBRAL_RIEGO:
            confianza = 1.0 if lectura.temperatura > self.UMBRAL_TEMP_ALTA else 0.95
            recs.append(Recomendacion(
                accion="riego_urgente",
                razon=(
                    f"Humedad del suelo en {lectura.humedad_suelo:.1f}% "
                    f"(umbral crítico: {self.UMBRAL_RIEGO}%). "
                    + (
                        f"Temperatura de {lectura.temperatura:.1f}°C acelera "
                        "la evaporación (Ley de Fick)."
                        if lectura.temperatura > self.UMBRAL_TEMP_ALTA
                        else "Se requiere riego inmediato."
                    )
                ),
                confianza=confianza,
                fuente="reglas",
            ))

        if lectura.temperatura > self.UMBRAL_TEMP_ALTA:
            recs.append(Recomendacion(
                accion="alerta_temperatura",
                razon=f"Temperatura de {lectura.temperatura:.1f}°C supera el umbral de {self.UMBRAL_TEMP_ALTA}°C.",
                confianza=0.9,
                fuente="reglas",
            ))

        if lectura.luminosidad < self.UMBRAL_LUZ_BAJA:
            recs.append(Recomendacion(
                accion="alerta_luz",
                razon=(
                    f"Luminosidad de {lectura.luminosidad:.0f} lux está por debajo "
                    f"de {self.UMBRAL_LUZ_BAJA} lux mínimos para fotosíntesis."
                ),
                confianza=0.88,
                fuente="reglas",
            ))

        if not recs:
            recs.append(Recomendacion(
                accion="estado_optimo",
                razon="Todas las variables ambientales dentro del rango óptimo.",
                confianza=0.99,
                fuente="reglas",
            ))

        return recs

    def predecir_humedad(self, historial: list[LecturaSensor]) -> float | None:
        if len(historial) < 3:
            return None
        # Predicción simple por tendencia lineal hasta tener datos para ML
        vals = [l.humedad_suelo for l in historial[:5]]
        pendiente = (vals[-1] - vals[0]) / len(vals)
        return max(0.0, min(100.0, vals[-1] + pendiente))


# ── Estrategia 2: Motor ML (Random Forest) ───────────────────────────────────

class MotorML(MotorIA):
    """
    Activo cuando hay ≥80 lecturas reales.
    RandomForestRegressor para predicción de humedad.
    IsolationForest para detectar lecturas anómalas.
    """

    MIN_MUESTRAS = 80

    def __init__(self):
        self._regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self._anomaly = IsolationForest(contamination=0.05, random_state=42)
        self._entrenado = False
        self._reglas = MotorReglas()   # fallback para análisis de reglas

    def entrenar(self, lecturas: list[LecturaSensor]) -> None:
        if len(lecturas) < self.MIN_MUESTRAS:
            return

        X = np.array([
            [l.temperatura, l.humedad_ambiental, l.luminosidad]
            for l in lecturas[:-1]
        ])
        y = np.array([l.humedad_suelo for l in lecturas[1:]])

        self._regressor.fit(X, y)
        self._anomaly.fit(X)
        self._entrenado = True

    def analizar(self, lectura: LecturaSensor) -> list[Recomendacion]:
        # El análisis semántico siempre usa reglas (100% precisión en escenarios definidos)
        recs = self._reglas.analizar(lectura)

        # Enriquecer con detección de anomalías si el modelo está listo
        if self._entrenado:
            x = np.array([[
                lectura.temperatura,
                lectura.humedad_ambiental,
                lectura.luminosidad,
            ]])
            pred = self._anomaly.predict(x)
            if pred[0] == -1:
                recs.append(Recomendacion(
                    accion="lectura_anomala",
                    razon="Isolation Forest detectó valores inusuales en esta lectura.",
                    confianza=0.75,
                    fuente="ml",
                ))

        return recs

    def predecir_humedad(self, historial: list[LecturaSensor]) -> float | None:
        if not self._entrenado or not historial:
            return self._reglas.predecir_humedad(historial)

        ultima = historial[0]
        x = np.array([[
            ultima.temperatura,
            ultima.humedad_ambiental,
            ultima.luminosidad,
        ]])
        return float(self._regressor.predict(x)[0])


# ── Factory del motor ─────────────────────────────────────────────────────────

def crear_motor(lecturas_disponibles: int) -> MotorIA:
    """
    Patrón Factory: devuelve el motor adecuado según el volumen de datos.
    """
    if lecturas_disponibles >= MotorML.MIN_MUESTRAS:
        return MotorML()
    return MotorReglas()
