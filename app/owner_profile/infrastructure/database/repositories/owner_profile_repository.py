from uuid import UUID

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.owner_profile.domain.entities.identity_document import (
    DocumentType,
    IdentityDocument,
)
from app.owner_profile.domain.entities.owner_profile import OwnerProfile
from app.owner_profile.domain.ports.output.owner_profile_repository_port import (
    OwnerProfileRepositoryPort,
)
from app.owner_profile.infrastructure.database.models import (
    IdentityDocumentModel,
    OwnerProfileModel,
)


class OwnerProfileRepository(OwnerProfileRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, profile: OwnerProfile) -> None:
        self._session.add(self._to_model(profile))

    async def exists_by_user_uuid(self, user_uuid: UUID) -> bool:
        return await self._exists(OwnerProfileModel.user_uuid == user_uuid)

    async def exists_by_ruc(self, ruc: str) -> bool:
        return await self._exists(OwnerProfileModel.ruc == ruc)

    async def exists_by_document(
        self, document_type: DocumentType, document_number: str
    ) -> bool:
        query = select(IdentityDocumentModel.uuid).where(
            IdentityDocumentModel.document_type == document_type.value,
            IdentityDocumentModel.document_number == document_number,
        )
        return (await self._session.execute(query)).first() is not None

    async def _exists(self, condition: ColumnElement[bool]) -> bool:
        query = select(OwnerProfileModel.uuid).where(condition)
        return (await self._session.execute(query)).first() is not None

    def _to_model(self, profile: OwnerProfile) -> OwnerProfileModel:
        return OwnerProfileModel(
            uuid=profile.uuid,
            user_uuid=profile.user_uuid,
            ruc=profile.ruc,
            address=profile.address,
            created_at=profile.created_at,
            updated_at=profile.updated_at,
            identity_documents=[
                self._document_to_model(document)
                for document in profile.identity_documents
            ],
        )

    @staticmethod
    def _document_to_model(document: IdentityDocument) -> IdentityDocumentModel:
        return IdentityDocumentModel(
            uuid=document.uuid,
            document_type=document.document_type.value,
            document_number=document.document_number,
            is_default=document.is_default,
            created_at=document.created_at,
        )
