from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/smartgarden"
    MQTT_HOST: str = "broker.hivemq.com"
    MQTT_PORT: int = 1883
    SECRET_KEY: str = "cambia-esta-clave-en-produccion"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
