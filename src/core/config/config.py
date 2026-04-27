from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/markettalento"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    YOLO_MODEL: str = "yolov8n.pt"
    LOG_LEVEL: str = "INFO"
    STREAMLIT_PORT: int = 8501

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
