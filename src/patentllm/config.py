from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    db_url: str = "sqlite:///./patentllm.db"
    index_path: str = "./.patentllm/index.pkl"
    ollama_base_url: str = "http://localhost:11434"
    default_model: str = "llama3.1:8b"
    default_top_k: int = 5
    model_config = SettingsConfigDict(env_prefix="PATENTLLM_", env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
