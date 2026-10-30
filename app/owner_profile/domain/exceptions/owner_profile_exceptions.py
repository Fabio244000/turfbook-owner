from app.owner_profile.domain.exceptions.domain_error import DomainError


class InvalidRucError(DomainError):
    pass


class InvalidDocumentNumberError(DomainError):
    pass


class InvalidAddressError(DomainError):
    pass


class InvalidOwnerProfileError(DomainError):
    """Every rule error found while building an owner profile, reported together."""

    def __init__(self, errors: list[DomainError]) -> None:
        super().__init__(' '.join(str(error) for error in errors))
        self.errors = errors


class OwnerProfileAlreadyExistsError(DomainError):
    pass


class DuplicateRucError(DomainError):
    pass


class DuplicateDocumentNumberError(DomainError):
    pass
