from functools import lru_cache
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    app_name: str = Field(default_factory=lambda: os.getenv("APP_NAME", "FitBuddy AI Fitness Plan Generator"))
    database_url: str = Field(default_factory=lambda: os.getenv("DATABASE_URL", "sqlite:///./fitbuddy.db"))
    google_api_key: str = Field(default_factory=lambda: os.getenv("GOOGLE_API_KEY", ""))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    cors_origins: list[str] = Field(default_factory=lambda: [
        item.strip() for item in os.getenv("CORS_ORIGINS", "http://127.0.0.1:8000,http://localhost:8000").split(",")
        if item.strip()
    ])
    min_plan_age: int = Field(default_factory=lambda: int(os.getenv("MIN_PLAN_AGE", "18")))

@lru_cache
def get_settings() -> Settings:
    return Settings()
