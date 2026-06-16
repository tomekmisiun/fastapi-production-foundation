import os
import re
from urllib.parse import urlsplit, urlunsplit

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

_SAFE_DATABASE_NAME = re.compile(r"^[A-Za-z0-9_]+$")


def _create_database_if_missing(database_url: str) -> None:
    parts = urlsplit(database_url)
    db_name = parts.path.lstrip("/")

    if not _SAFE_DATABASE_NAME.match(db_name):
        raise ValueError(f"Unsafe test database name: {db_name!r}")

    admin_url = urlunsplit(parts._replace(path="/postgres"))
    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

    try:
        with admin_engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": db_name},
            ).first()

            if exists is None:
                connection.execute(text(f'CREATE DATABASE "{db_name}"'))
    finally:
        admin_engine.dispose()


# Only pytest-xdist workers need a per-worker database provisioned on the fly.
# Serial runs use the pre-provisioned TEST_DATABASE_URL as-is.
if os.environ.get("PYTEST_XDIST_WORKER"):
    _create_database_if_missing(settings.test_database_url)

engine = create_engine(settings.test_database_url)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def reset_test_database() -> None:
    with engine.connect() as connection:
        connection.execution_options(isolation_level="AUTOCOMMIT")
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


def run_test_migrations() -> None:
    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", settings.test_database_url)
    command.upgrade(alembic_config, "head")
