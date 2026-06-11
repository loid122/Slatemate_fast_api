# app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Security
    secret_key: str = "change-this-in-prod"
    debug: bool = True

    # Database
    db_url: str = "postgresql+psycopg2://myuser:mypassword@127.0.0.1:5432/parentalcontrol"

    # CORS
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "0.0.0.0"]

    # JWT (replacement for DRF SimpleJWT)
    jwt_secret: str = "super-secret-jwt-key"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30

    class Config:
        env_file = ".env"   # load from .env if present

settings = Settings()
