from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.owner_profile.domain.entities.identity_document import DocumentType


class IdentityDocumentRequest(BaseModel):
    document_type: DocumentType
    document_number: str


class OwnerProfileRequest(BaseModel):
    """Fields outside the contract (e.g. a user_uuid) are ignored: the user is the
    token's."""

    ruc: str
    identity_document: IdentityDocumentRequest
    address: str | None = None


class IdentityDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_type: DocumentType
    document_number: str
    is_default: bool


class RegisterOwnerProfileData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    user_uuid: UUID
    ruc: str
    identity_documents: list[IdentityDocumentResponse]
    address: str | None
    created_at: datetime
