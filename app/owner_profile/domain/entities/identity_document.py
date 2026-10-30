from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID, uuid4

from app.owner_profile.domain.constants import DNI_PATTERN, DOCUMENT_NUMBER_PATTERN
from app.owner_profile.domain.exceptions import InvalidDocumentNumberError
from app.owner_profile.domain.messages import INVALID_DNI, INVALID_DOCUMENT_NUMBER


class DocumentType(StrEnum):
    DNI = 'DNI'
    PASSPORT = 'PASSPORT'
    CARNET_EXTRANJERIA = 'CARNET_EXTRANJERIA'


@dataclass
class IdentityDocument:
    document_type: DocumentType
    document_number: str
    is_default: bool
    created_at: datetime
    uuid: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.document_type is DocumentType.DNI:
            self._check(DNI_PATTERN.fullmatch(self.document_number), INVALID_DNI)
        else:
            self._check(
                DOCUMENT_NUMBER_PATTERN.fullmatch(self.document_number),
                INVALID_DOCUMENT_NUMBER,
            )

    @staticmethod
    def _check(valid: object, message: str) -> None:
        if not valid:
            raise InvalidDocumentNumberError(message)
