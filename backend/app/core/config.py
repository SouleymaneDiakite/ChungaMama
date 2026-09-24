from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ChungaMama"

    DATABASE_URL: str = "postgresql://chungamama:chungamama@localhost:5432/chungamama"
    SECRET_KEY: str = "change-this-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Mane's conversational assistant service — called via the clean API
    # boundary agreed on: {patient_context, message} -> {intent, entities,
    # risk_level, reply, escalate}
    ASSISTANT_SERVICE_URL: str = "http://localhost:9000/chat"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
