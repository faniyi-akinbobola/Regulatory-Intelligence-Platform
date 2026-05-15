from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    debug: bool = False
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Postgres
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/regulatory_platform" 

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = 'regulatory_docs'

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    secret_key: str = "placeholder"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # LLM
    llm_provider: str = "openai"
    llm_base_url: str | None = None
    llm_api_key: str | None = None
    llm_model: str = "gpt-4o-mini"

    # Embeddings
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dim: int = 1536

settings = Settings()


