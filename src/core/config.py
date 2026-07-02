# config.py
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM
    llm_provider: str = Field("gemini", env="LLM_PROVIDER")
    llm_model: str = Field("gemini-3.1-flash-lite", env="LLM_MODEL")
    vision_llm_model: Optional[str] = Field(None, env="VISION_LLM_MODEL")
    docx_llm_model: Optional[str] = Field(None, env="DOCX_LLM_MODEL")
    max_doc_pages: int = Field(6, env="MAX_DOC_PAGES")
    doc_gen_max_retries: int = Field(3, env="DOC_GEN_MAX_RETRIES")


    # Google / Firebase
    project_id: Optional[str] = Field(None, env="PROJECT_ID")
    firebase_project_id: Optional[str] = Field(None, env="FIREBASE_PROJECT_ID")
    firebase_storage_bucket: Optional[str] = Field(None, env="FIREBASE_STORAGE_BUCKET")
    firebase_credentials_path: Optional[str] = Field(None, env="FIREBASE_CREDENTIALS_PATH")

    # API keys (never set defaults here)
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")

    # Other
    LOCAL_TEST: bool = Field(False, env="LOCAL_TEST")
    allow_firebase_mocks: bool = Field(False, env="ALLOW_FIREBASE_MOCKS")
    redis_url: Optional[str] = Field("redis://localhost:6379/0", env="REDIS_URL")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
