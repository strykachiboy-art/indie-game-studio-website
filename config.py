import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base application configuration, read from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # PostgreSQL connection string. Falls back to a local dev database.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/gamestudio",
    )

    # SQLAlchemy expects "postgresql://" but some providers hand out
    # "postgres://" — normalize it so the app always boots.
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace(
            "postgres://", "postgresql://", 1
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
