from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "sqlite:///./recommendations.db"
    
    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://redis:6379"
    
    # LLM
    LOCALAI_BASE_URL: str = "http://host.docker.internal:8080/v1"
    LLM_MODEL: str = "gemma-3-12b-it"
    MODERATION_MODEL: str = "llama-guard-3-8b"
    EMBEDDING_MODEL: str = "qwen3-embedding-4b"
    OPENAI_API_KEY: str = "sk-something"
    OPENAI_API_BASE: str = "http://host.docker.internal:8080/v1"
    MODEL_TYPE: str = "OpenAI"
    MODEL_N_CTX: int = 1024
    EMBEDDING_CTX_LENGTH: int = 8192
    
    # ChromaDB
    #CHROMA_HOST: str = "http://chromadb:8000"
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    
    # ClickHouse
    CLICKHOUSE_HOST: str = "localhost"
    CLICKHOUSE_PORT: int = 9000
    CLICKHOUSE_USER: str = "default"
    CLICKHOUSE_PASSWORD: str = "default"
    CLICKHOUSE_DATABASE: str = "default"
    
    
    class Config:
        env_file = ".env"

settings = Settings()