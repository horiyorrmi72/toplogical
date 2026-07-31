from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FinBank Digital Banking"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "SUPER_SECRET_KEY_CHANGE_THIS_IN_PRODUCTION_123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    # DATABASE_URL: str = "sqlite+aiosqlite:///./finbank.db"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
