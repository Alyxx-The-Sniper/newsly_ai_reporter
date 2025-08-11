import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _normalize_db(url: str) -> str:
    if not url:
        return ""
    return "postgresql+psycopg://" + url[len("postgres://"):] if url.startswith("postgres://") else url


@dataclass
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    database_url: str = _normalize_db(os.getenv("DATABASE_URL", "sqlite:///./news_reports.db"))
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    s3_prefix: str = os.getenv("S3_PREFIX", "reports/")
    port: int = int(os.getenv("PORT", "8000"))


settings = Settings()