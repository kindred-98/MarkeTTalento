from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///data/markettalento.db"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8002
    YOLO_MODEL: str = "models/yolov8n.pt"
    LOG_LEVEL: str = "INFO"
    STREAMLIT_PORT: int = 8501
    SECRET_KEY: str = "markettalento-secret-key-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
