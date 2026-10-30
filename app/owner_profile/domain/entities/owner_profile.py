from dataclasses import dataclass, field
from datetime import datetime
from typing import Self
from uuid import UUID, uuid4

from app.owner_profile.domain.constants import (
    ADDRESS_PATTERN,
    MAX_ADDRESS_LENGTH,
    RUC_PATTERN,
)
from app.owner_profile.domain.entities.identity_document import (
    DocumentType,
    IdentityDocument,
)
from app.owner_profile.domain.exceptions import (
    DomainError,
    InvalidAddressError,
    InvalidDocumentNumberError,
    InvalidOwnerProfileError,
    InvalidRucError,
)
from app.owner_profile.domain.messages import (
    ADDRESS_TOO_LONG,
    INVALID_ADDRESS,
    INVALID_RUC,
)


@dataclass
class OwnerProfile:
    user_uuid: UUID
    ruc: str
    identity_documents: list[IdentityDocument]
    address: str | None
    created_at: datetime
    updated_at: datetime
    uuid: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        errors = [*_ruc_errors(self.ruc), *_address_errors(self.address)]
        if errors:
            raise InvalidOwnerProfileError(errors)

    @classmethod
    def register(
        cls,
        user_uuid: UUID,
        ruc: str,
        document_type: DocumentType,
        document_number: str,
        address: str | None,
        now: datetime,
    ) -> Self:
        """A new profile whose only document is the default one. Every invalid field
        of the profile and its document is reported in one InvalidOwnerProfileError."""
        errors: list[DomainError] = []
        documents: list[IdentityDocument] = []
        try:
            documents.append(
                IdentityDocument(
                    document_type=document_type,
                    document_number=document_number,
                    is_default=True,
                    created_at=now,
                )
            )
        except InvalidDocumentNumberError as error:
            errors.append(error)
        try:
            profile = cls(
                user_uuid=user_uuid,
                ruc=ruc,
                identity_documents=documents,
                address=address,
                created_at=now,
                updated_at=now,
            )
        except InvalidOwnerProfileError as error:
            errors.extend(error.errors)
        if errors:
            raise InvalidOwnerProfileError(errors)
        return profile


def _ruc_errors(ruc: str) -> list[DomainError]:
    return [] if RUC_PATTERN.fullmatch(ruc) else [InvalidRucError(INVALID_RUC)]


def _address_errors(address: str | None) -> list[DomainError]:
    if address is None:
        return []
    if not ADDRESS_PATTERN.fullmatch(address):
        return [InvalidAddressError(INVALID_ADDRESS)]
    if len(address) > MAX_ADDRESS_LENGTH:
        return [InvalidAddressError(ADDRESS_TOO_LONG)]
    return []
