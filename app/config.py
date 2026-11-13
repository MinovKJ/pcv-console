"""
PCV Console – application settings
All values are loaded from environment variables / .env file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "pcvuser"
    mysql_password: str = "pcvpass"
    mysql_db: str = "pcvconsole"

    # MongoDB
    mongo_host: str = "localhost"
    mongo_port: int = 27017
    mongo_user: str = "pcvmongo"
    mongo_password: str = "mongopass"
    mongo_db: str = "pcvconsole"

    # JWT
    jwt_secret_key: str = "CHANGE_ME"
    jwt_algorithm: str = "HS256"
    jwt_access_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # LLM
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # App
    app_env: str = "development"
    app_debug: bool = False

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_db}"
        )

    @property
    def mongo_uri(self) -> str:
        return (
            f"mongodb://{self.mongo_user}:{self.mongo_password}"
            f"@{self.mongo_host}:{self.mongo_port}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
