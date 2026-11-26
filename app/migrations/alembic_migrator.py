from pathlib import Path

from alembic.command import downgrade, upgrade
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import NullPool


class DatabaseNotReadyError(Exception):
    """The service database cannot be reached: not provisioned yet, wrong
    credentials in its secret, or the instance is unreachable."""


DATABASE_NOT_READY_MESSAGE = 'Database not provisioned or unreachable'


class AlembicMigrator:
    def __init__(self, ini_path: Path, database_url: str) -> None:
        self._database_url = database_url
        self._config = Config(str(ini_path))
        # env.py reads it: Alembic would otherwise take the URL from settings.
        self._config.attributes['database_url'] = database_url

    def upgrade(self) -> None:
        try:
            upgrade(self._config, 'head')
        except OperationalError as error:
            raise _not_ready(error) from error

    def current(self) -> str | None:
        """The revision of the database; None at base (no migration applied)."""
        engine = create_engine(self._database_url, poolclass=NullPool)
        try:
            with engine.connect() as connection:
                return MigrationContext.configure(connection).get_current_revision()
        except OperationalError as error:
            raise _not_ready(error) from error
        finally:
            engine.dispose()

    def downgrade(self, revision: str) -> str | None:
        """Undoes the migrations down to `revision` ('base': all of them) and returns
        the revision reached. Runs with the code of the deploy that brought them: the
        only one that has their files."""
        try:
            downgrade(self._config, revision)
        except OperationalError as error:
            raise _not_ready(error) from error
        return self.current()


def _not_ready(error: OperationalError) -> DatabaseNotReadyError:
    return DatabaseNotReadyError(f'{DATABASE_NOT_READY_MESSAGE}: {error.orig}')
