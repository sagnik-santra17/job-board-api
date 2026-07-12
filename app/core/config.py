from pydantic_settings import BaseSettings, SettingsConfigDict


# ---------------------------------------------------------------------------- #


class Settings(BaseSettings):

    APP_NAME: str = "Job-Board-API"
    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

settings = Settings()