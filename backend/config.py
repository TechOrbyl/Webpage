from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = ""
    admin_username: str = "admin"
    admin_password: str = "orbyl2026"
    session_secret: str = "orbyl-local-session-secret"
    app_name: str = "ORBYL API"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
