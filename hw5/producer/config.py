from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    kafka_bootstrap_servers: str = "kafka-1:9092,kafka-2:9093"
    kafka_topic: str = "movie-events"
    schema_registry_url: str = "http://schema-registry:8081"
    generator_enabled: bool = True
    generator_interval_seconds: float = 2.0
    generator_backfill_days: int = 9
    producer_port: int = 8000

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
