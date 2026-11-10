from uuid import UUID

from app.owner_profile.application.dtos.outputs import (
    IdentityDocumentDetails,
    OwnerProfileDetails,
)
from app.owner_profile.application.exceptions import OwnerProfileNotFoundError
from app.owner_profile.application.ports.driving.get_owner_profile_port import (
    GetOwnerProfilePort,
)
from app.owner_profile.domain.entities.owner_profile import OwnerProfile
from app.owner_profile.domain.ports.driven.unit_of_work_port import UnitOfWorkPort


class GetOwnerProfileUseCase(GetOwnerProfilePort):
    def __init__(self, uow: UnitOfWorkPort) -> None:
        self._uow = uow

    async def execute(self, user_uuid: UUID) -> OwnerProfileDetails:
        async with self._uow:
            profile = await self._uow.owner_profiles.get_by_user_uuid(user_uuid)
        if profile is None:
            raise OwnerProfileNotFoundError()
        return _to_owner_profile_details(profile)


def _to_owner_profile_details(profile: OwnerProfile) -> OwnerProfileDetails:
    return OwnerProfileDetails(
        uuid=profile.uuid,
        user_uuid=profile.user_uuid,
        ruc=profile.ruc,
        address=profile.address,
        created_at=profile.created_at,
        identity_documents=tuple(
            IdentityDocumentDetails(
                document_type=document.document_type.value,
                document_number=document.document_number,
                is_default=document.is_default,
            )
            for document in profile.identity_documents
        ),
    )
