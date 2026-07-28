import os
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base application configuration, read from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")

    # --- Database URL -----------------------------------------------
    # Only fall back to local dev DB when explicitly running in dev mode.
    # In production, a missing DATABASE_URL should fail loudly at boot
    # instead of silently connecting to a nonexistent local Postgres —
    # that's what turns into a mystery "Internal Server Error" later.
    _raw_url = os.environ.get("DATABASE_URL")

    if not _raw_url:
        if os.environ.get("FLASK_ENV") == "production" or os.environ.get("ENV") == "production":
            raise RuntimeError(
                "DATABASE_URL is not set. Set it in your deploy platform's "
                "environment variables — do not rely on a .env file in production."
            )
        _raw_url = "postgresql://postgres:postgres@localhost:5432/gamestudio"

    # SQLAlchemy expects "postgresql://" but some providers hand out
    # "postgres://" — normalize it so the app always boots.
    if _raw_url.startswith("postgres://"):
        _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)

    SQLALCHEMY_DATABASE_URI = _raw_url

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Engine options -----------------------------------------------
    # If you're connecting through Supabase's transaction pooler (port 6543),
    # pgbouncer is already pooling connections on its end. Layering
    # SQLAlchemy's own connection pool on top of that causes stale/broken
    # connections after idle periods — a common source of intermittent
    # 500s that only show up after a redeploy or period of inactivity.
    # NullPool tells SQLAlchemy "don't pool, open fresh each time" and
    # lets pgbouncer do the actual pooling.
    #
    # If instead you're on the session pooler (port 5432) or a direct
    # connection, you can drop NullPool and use pool_size/max_overflow
    # normally.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,   # test connection liveness before using it
        "poolclass": NullPool,   # let pgbouncer own pooling (transaction mode)
    }