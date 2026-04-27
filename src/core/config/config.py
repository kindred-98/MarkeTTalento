from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///data/markettalento.db"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8002
    YOLO_MODEL: str = "models/yolov8n.pt"
    LOG_LEVEL: str = "INFO"
    STREAMLIT_PORT: int = 8501

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
