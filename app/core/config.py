from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # PostgreSQL
    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "regulations"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Embedding model
    embedding_model_name: str = "BAAI/bge-base-en-v1.5"
    embedding_dimension: int = 768

    # LLM
    llm_base_url: str = "http://localhost:11434"  # Ollama default
    llm_model_name: str = "qwen2.5:14b"

    @property
    def postgres_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()