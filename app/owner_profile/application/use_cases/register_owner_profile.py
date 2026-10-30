from uuid import UUID

from app.owner_profile.application.messages import (
    DUPLICATE_DOCUMENT,
    DUPLICATE_RUC,
    PROFILE_ALREADY_EXISTS,
)
from app.owner_profile.domain.entities.identity_document import DocumentType
from app.owner_profile.domain.entities.owner_profile import OwnerProfile
from app.owner_profile.domain.exceptions import (
    DuplicateDocumentNumberError,
    DuplicateRucError,
    OwnerProfileAlreadyExistsError,
)
from app.owner_profile.domain.ports.input.register_owner_profile_port import (
    RegisterOwnerProfilePort,
)
from app.owner_profile.domain.ports.output.clock_port import ClockPort
from app.owner_profile.domain.ports.output.unit_of_work_port import UnitOfWorkPort


class RegisterOwnerProfileUseCase(RegisterOwnerProfilePort):
    def __init__(self, uow: UnitOfWorkPort, clock: ClockPort) -> None:
        self._uow = uow
        self._clock = clock

    async def execute(
        self,
        user_uuid: UUID,
        ruc: str,
        document_type: DocumentType,
        document_number: str,
        address: str | None = None,
    ) -> OwnerProfile:
        profile = OwnerProfile.register(
            user_uuid=user_uuid,
            ruc=ruc,
            document_type=document_type,
            document_number=document_number,
            address=address,
            now=self._clock.now(),
        )
        async with self._uow:
            await self._ensure_unique(profile)
            await self._uow.owner_profiles.add(profile)
            await self._uow.commit()
        return profile

    async def _ensure_unique(self, profile: OwnerProfile) -> None:
        """Asks in the contract's order: the user's profile, the RUC, the document."""
        profiles = self._uow.owner_profiles
        if await profiles.exists_by_user_uuid(profile.user_uuid):
            raise OwnerProfileAlreadyExistsError(PROFILE_ALREADY_EXISTS)
        if await profiles.exists_by_ruc(profile.ruc):
            raise DuplicateRucError(DUPLICATE_RUC)
        for document in profile.identity_documents:
            if await profiles.exists_by_document(
                document.document_type, document.document_number
            ):
                raise DuplicateDocumentNumberError(DUPLICATE_DOCUMENT)
