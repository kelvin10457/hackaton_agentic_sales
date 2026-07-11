import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "changeme")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
    PORT: int = int(os.getenv("PORT", 8000))


settings = Settings()

__all__ = ["settings", "Settings"]
