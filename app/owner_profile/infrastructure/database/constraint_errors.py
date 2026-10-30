import psycopg
from sqlalchemy.exc import IntegrityError

from app.owner_profile.application.messages import (
    DUPLICATE_DOCUMENT,
    DUPLICATE_RUC,
    PROFILE_ALREADY_EXISTS,
)
from app.owner_profile.domain.exceptions import (
    DomainError,
    DuplicateDocumentNumberError,
    DuplicateRucError,
    OwnerProfileAlreadyExistsError,
)
from app.owner_profile.infrastructure.database.models import (
    DOCUMENT_KEY,
    PROFILE_RUC_KEY,
    PROFILE_USER_KEY,
)

# Unique constraints whose violation is a concurrent duplicate the use case could not
# see: the domain error it means and its message.
DUPLICATE_CONSTRAINTS: dict[str, tuple[type[DomainError], str]] = {
    PROFILE_USER_KEY: (OwnerProfileAlreadyExistsError, PROFILE_ALREADY_EXISTS),
    PROFILE_RUC_KEY: (DuplicateRucError, DUPLICATE_RUC),
    DOCUMENT_KEY: (DuplicateDocumentNumberError, DUPLICATE_DOCUMENT),
}


def to_domain_error(error: IntegrityError) -> DomainError | None:
    """The domain meaning of a violated constraint, or None when it has none."""
    meaning = DUPLICATE_CONSTRAINTS.get(_constraint_name(error))
    if meaning is None:
        return None
    error_type, message = meaning
    return error_type(message)


def _constraint_name(error: IntegrityError) -> str:
    if isinstance(error.orig, psycopg.Error):
        return error.orig.diag.constraint_name or ''
    return ''
