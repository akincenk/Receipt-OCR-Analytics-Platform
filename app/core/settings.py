import os

from pydantic import BaseModel


class Settings(BaseModel):
    # Default is a local dev database; set DATABASE_URL in any real environment.
    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/receipts")
    upload_dir: str = os.getenv("UPLOAD_DIR", "./uploads")
    max_upload_bytes: int = int(os.getenv("MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))
    # Comma-separated list of allowed browser origins; empty disables CORS.
    cors_origins: list[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

settings = Settings()
