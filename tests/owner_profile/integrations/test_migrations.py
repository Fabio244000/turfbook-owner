from collections.abc import Iterator
from uuid import uuid4

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from alembic import command
from app.migrations.handler import ALEMBIC_INIT_PATH
from config.settings import settings

SERVICE_TABLES = {'owner_profiles', 'identity_documents'}


def _tables(schema: str) -> set[str]:
    engine = create_engine(settings.database_url)
    try:
        return set(inspect(engine).get_table_names(schema=schema))
    finally:
        engine.dispose()


def _run_sql(statement: str) -> None:
    engine = create_engine(settings.database_url)
    try:
        with engine.begin() as connection:
            connection.execute(text(statement))
    finally:
        engine.dispose()


@pytest.fixture
def own_schema(monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    """A throwaway schema that Alembic migrates instead of `public`: a downgrade
    drops tables, so it must never touch the tables (and data) everyone else uses."""
    schema = f'migrations_test_{uuid4().hex}'
    _run_sql(f'CREATE SCHEMA {schema}')
    # libpq reads PGOPTIONS on every new connection, Alembic's included.
    monkeypatch.setenv('PGOPTIONS', f'-c search_path={schema}')
    yield schema
    monkeypatch.undo()
    _run_sql(f'DROP SCHEMA {schema} CASCADE')


class TestMigrations:
    """Runs Alembic for real: synchronous because Alembic's env.py runs its own
    event loop."""

    def test_upgrade_creates_the_tables_and_downgrade_removes_them(
        self, own_schema: str
    ) -> None:
        config = Config(str(ALEMBIC_INIT_PATH))

        command.upgrade(config, 'head')
        tables_after_upgrade = _tables(own_schema)
        command.downgrade(config, 'base')

        assert tables_after_upgrade >= SERVICE_TABLES
        assert SERVICE_TABLES.isdisjoint(_tables(own_schema))
