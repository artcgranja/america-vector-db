# src/app/core/config.py
import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    database_url: str = os.getenv("DATABASE_URL")
    chunk_size: int = 1000
    chunk_overlap: int = 100
    host: str = "localhost"
    port: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()