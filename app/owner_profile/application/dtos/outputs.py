from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class IdentityDocumentDetails:
    document_type: str
    document_number: str
    is_default: bool


@dataclass(frozen=True)
class OwnerProfileDetails:
    uuid: UUID
    user_uuid: UUID
    ruc: str
    address: str | None
    created_at: datetime
    identity_documents: tuple[IdentityDocumentDetails, ...]
