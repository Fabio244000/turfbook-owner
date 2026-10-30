from abc import ABC, abstractmethod
from uuid import UUID

from app.owner_profile.domain.entities.identity_document import DocumentType
from app.owner_profile.domain.entities.owner_profile import OwnerProfile


class OwnerProfileRepositoryPort(ABC):
    @abstractmethod
    async def add(self, profile: OwnerProfile) -> None:
        """Stores the profile together with its identity documents."""

    @abstractmethod
    async def exists_by_user_uuid(self, user_uuid: UUID) -> bool: ...

    @abstractmethod
    async def exists_by_ruc(self, ruc: str) -> bool: ...

    @abstractmethod
    async def exists_by_document(
        self, document_type: DocumentType, document_number: str
    ) -> bool: ...
