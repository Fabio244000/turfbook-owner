from abc import ABC, abstractmethod
from uuid import UUID

from app.owner_profile.domain.entities.identity_document import DocumentType
from app.owner_profile.domain.entities.owner_profile import OwnerProfile


class RegisterOwnerProfilePort(ABC):
    @abstractmethod
    async def execute(
        self,
        user_uuid: UUID,
        ruc: str,
        document_type: DocumentType,
        document_number: str,
        address: str | None = None,
    ) -> OwnerProfile: ...
