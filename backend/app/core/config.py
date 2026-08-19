from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    db_host: str
    db_port: int = 5432
    db_name: str
    db_test_name: str = "mini_crm_test"
    db_user: str
    db_password: SecretStr

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.db_user,
            password=self.db_password.get_secret_value(),
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
        )
    @property
    def test_database_url(self) -> URL:
        return self.database_url.set(database=self.db_test_name)


@lru_cache
def get_settings() -> Settings:
    return Settings()