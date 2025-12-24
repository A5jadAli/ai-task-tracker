from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Coding Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    OPENAI_TEMPERATURE: float = 0.1
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Storage
    PROJECTS_BASE_PATH: Path = Path("./storage/projects")
    PLANS_PATH: Path = Path("./storage/plans")
    REPORTS_PATH: Path = Path("./storage/reports")
    MEMORY_PATH: Path = Path("./storage/memory")
    
    # Git Configuration
    GIT_USER_NAME: str = "AI Coding Assistant"
    GIT_USER_EMAIL: str = "ai@assistant.com"
    MAIN_BRANCH_NAMES: list = ["main", "dev", "development", "master"]
    
    # Notification
    NOTIFICATION_WEBHOOK_URL: Optional[str] = None
    NOTIFICATION_EMAIL: Optional[str] = None
    
    # Agent Configuration
    MAX_ITERATIONS: int = 10
    PLANNING_TIMEOUT: int = 300
    DEVELOPMENT_TIMEOUT: int = 1800
    TESTING_TIMEOUT: int = 600
    
    # Vector Store
    VECTOR_STORE_TYPE: str = "chroma"
    CHROMA_PERSIST_DIRECTORY: Path = Path("./storage/memory/chroma")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

# Ensure directories exist
settings.PROJECTS_BASE_PATH.mkdir(parents=True, exist_ok=True)
settings.PLANS_PATH.mkdir(parents=True, exist_ok=True)
settings.REPORTS_PATH.mkdir(parents=True, exist_ok=True)
settings.MEMORY_PATH.mkdir(parents=True, exist_ok=True)
settings.CHROMA_PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)
