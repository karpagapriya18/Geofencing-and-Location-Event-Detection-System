from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GeoSentinel Field API"
    database_url: str = "sqlite:///./geofence.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    gps_accuracy_buffer_meters: float = 15.0
    token_secret: str = "change-this-development-secret"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="GEOFENCE_")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
