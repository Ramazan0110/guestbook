from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Вся конфигурация приложения. Значения берутся из окружения и файла .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "guestbook"
    db_user: str = "guestbook"
    db_password: SecretStr = SecretStr("")

    # Версия образа. Ставится при сборке (ARG APP_VERSION), в рантайме берётся из окружения.
    app_version: str = "dev"

    @property
    def dsn(self) -> str:
        return (
            f"host={self.db_host} port={self.db_port} dbname={self.db_name} "
            f"user={self.db_user} password={self.db_password.get_secret_value()}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
