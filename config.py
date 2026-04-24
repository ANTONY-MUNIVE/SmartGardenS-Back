from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./smartgarden.db"
    MQTT_HOST: str = "localhost"
    MQTT_PORT: int = 1883

    class Config:
        env_file = ".env"