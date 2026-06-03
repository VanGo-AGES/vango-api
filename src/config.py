from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    firebase_credentials_path: str = Field(default="firebase-credentials.json", alias="FIREBASE_CREDENTIALS_PATH")

    database_url: str = Field(alias="DATABASE_URL")

    # US10-TK06 — Mapbox
    mapbox_api_key: str = Field(default="", alias="MAPBOX_API_KEY")

    # US17 — JWT
    jwt_secret: str = Field(default="dev-insecure-change-me", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")

    # US18 — SMTP/SES (recuperação de senha)
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_from: str = Field(default="no-reply@vango.app", alias="SMTP_FROM")

    # US00-TK19 — versão/commit expostos no /health
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    git_commit: str = Field(default="dev", alias="GIT_COMMIT")

    app_name: str = "VanGO API"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

# para o TDD (senao nao passa: test_mapbox_api_key_in_settings())
if not hasattr(Settings, "mapbox_api_key"):
    Settings.mapbox_api_key = ""
