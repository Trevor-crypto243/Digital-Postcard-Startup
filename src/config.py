import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "Digital Postcard QA Pipeline"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "agentic-demo-secret-key-999" # In prod, pull from env
    ADMIN_API_KEY: str = "agentic-demo-key-123"
    
    # Observability
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "interview-trial"
    
    # AI Config
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.1
    
    # Database
    DATABASE_URL: str = "postgresql://admin:password@localhost:5432/agentic_db"
    DATABASE_SYNC_URL: str = "postgresql+psycopg://admin:password@localhost:5432/agentic_db"
    
    # Slack Integration
    SLACK_WEBHOOK_URL: Optional[str] = None
    MODERATION_CHANNEL: str = "#moderation"
    
    # Email Integration
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    SENDER_EMAIL: str = "noreply@postcard-startup.com"
    
    # Operational Constants
    MIN_TEXT_LENGTH: int = 5
    MAX_TEXT_LENGTH: int = 1000
    RATE_LIMIT_EVALUATE: str = "5/minute"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
