from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        extra="ignore",
    )

    app_env: str = "development"
    jwt_secret: str = "dev-only-change-me"
    jwt_expire_minutes: int = 60 * 24 * 7
    database_url: str = "postgresql+psycopg2://careerpilot:careerpilot@localhost:5432/careerpilot"
    redis_url: str = "redis://localhost:6380/0"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-120b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    tavily_api_key: str | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        if value.startswith("postgres://"):
            return "postgresql+psycopg2://" + value[len("postgres://") :]
        if value.startswith("postgresql://") and "+" not in value.split("://", 1)[0]:
            return "postgresql+psycopg2://" + value[len("postgresql://") :]
        return value

    @field_validator("groq_api_key", "tavily_api_key", mode="before")
    @classmethod
    def blank_to_none(cls, value: str | None) -> str | None:
        if value is None or (isinstance(value, str) and not value.strip()):
            return None
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def llm_mode(self) -> str:
        # Groq is the exclusive LLM provider throughout CareerPilot AI.
        # Even if OPENAI_API_KEY exists in .env or the environment, it is never used.
        return "groq" if self.groq_api_key else "demo"

    @property
    def search_mode(self) -> str:
        return "tavily" if self.tavily_api_key else "demo"


settings = Settings()
