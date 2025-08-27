import os
from typing import Literal

class Config:
    APP_ENV: Literal["dev", "prod"] = os.getenv("APP_ENV", "dev")
    DB_PATH: str = os.getenv("DB_PATH", "/app/data/app.db")
    DAILY_SIZE: int = int(os.getenv("DAILY_SIZE", "10"))
    PREFLOP_MC: int = int(os.getenv("PREFLOP_MC", "200000"))
    RNG_SEED_SALT: str = os.getenv("RNG_SEED_SALT", "poker_equity_salt_2024")
    
    # Cache settings
    CACHE_MAX_SIZE: int = int(os.getenv("CACHE_MAX_SIZE", "100000"))
    CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS", str(30*24*3600)))  # 30 days
    
    # API settings
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list[str] = ["*"] if APP_ENV == "dev" else []

config = Config()