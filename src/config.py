from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    firebase_credentials_path: str = Field(default="firebase-credentials.json", alias="FIREBASE_CREDENTIALS_PATH")

    database_url: str = Field(alias="DATABASE_URL")

    app_name: str = "VanGO API"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
