import os
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    _is_prod = (
        os.environ.get("VERCEL") == "1"
        or os.environ.get("FLASK_ENV") == "production"
        or os.environ.get("ENV") == "production"
    )

    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        if _is_prod:
            raise RuntimeError("SECRET_KEY is not set.")
        SECRET_KEY = "dev-secret-change-me"

    _raw_url = os.environ.get("DATABASE_URL")

    if not _raw_url:
        if _is_prod:
            raise RuntimeError("DATABASE_URL is not set.")
        _raw_url = "postgresql://postgres:postgres@localhost:5432/gamestudio"

    if _raw_url.startswith("postgres://"):
        _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)

    MAX_CONTENT_LENGTH = 3 * 1024 * 1024

    SQLALCHEMY_DATABASE_URI = _raw_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "poolclass": NullPool,
    }

    RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "onboarding@resend.dev")
