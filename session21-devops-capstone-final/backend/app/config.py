"""Settings, read from the environment.

Everything the app needs to talk to the outside world is injected rather than
hardcoded, so the same image runs under Compose, under Helm, and in tests.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Compose and Helm both override this. The default points at a local
    # Postgres so `uvicorn app.main:app` works without a .env file.
    database_url: str = "postgresql+psycopg://campusdesk:campusdesk@localhost:5432/campusdesk"

    app_name: str = "CampusDesk"
    # Tests set this to skip the table-creation hook and use their own engine.
    testing: bool = False


settings = Settings()
