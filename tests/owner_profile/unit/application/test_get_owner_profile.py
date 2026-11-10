from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.owner_profile.application.dtos.outputs import (
    IdentityDocumentDetails,
    OwnerProfileDetails,
)
from app.owner_profile.application.exceptions import OwnerProfileNotFoundError
from app.owner_profile.application.use_cases.get_owner_profile import (
    GetOwnerProfileUseCase,
)
from app.owner_profile.application.use_cases.register_owner_profile import (
    RegisterOwnerProfileUseCase,
)
from app.owner_profile.domain.entities.identity_document import DocumentType
from tests.fakes.owner_profile import FakeClock, FakeUnitOfWork

NOW = datetime(2026, 10, 29, 15, 30, tzinfo=UTC)
ADDRESS = 'Ayacucho-Huamanga-Ayacucho:Pasaje Los Ángeles Mz 24 Lt A'


async def _register_owner(
    uow: FakeUnitOfWork,
    user_uuid: UUID,
    ruc: str = '10712345671',
    document_number: str = '71234567',
    address: str | None = ADDRESS,
) -> UUID:
    """Registers an owner through its use case (written before the DTOs, it takes the
    domain's DocumentType); returns only the profile's uuid."""
    profile = await RegisterOwnerProfileUseCase(uow=uow, clock=FakeClock(NOW)).execute(
        user_uuid=user_uuid,
        ruc=ruc,
        document_type=DocumentType.DNI,
        document_number=document_number,
        address=address,
    )
    return profile.uuid


class TestGetOwnerProfile:
    async def test_returns_the_profile_the_user_registered(self) -> None:
        uow = FakeUnitOfWork()
        user_uuid = uuid4()
        profile_uuid = await _register_owner(uow, user_uuid)

        details = await GetOwnerProfileUseCase(uow=uow).execute(user_uuid=user_uuid)

        assert details == OwnerProfileDetails(
            uuid=profile_uuid,
            user_uuid=user_uuid,
            ruc='10712345671',
            address=ADDRESS,
            created_at=NOW,
            identity_documents=(
                IdentityDocumentDetails(
                    document_type='DNI', document_number='71234567', is_default=True
                ),
            ),
        )

    async def test_returns_no_address_when_none_was_registered(self) -> None:
        uow = FakeUnitOfWork()
        user_uuid = uuid4()
        await _register_owner(uow, user_uuid, address=None)

        details = await GetOwnerProfileUseCase(uow=uow).execute(user_uuid=user_uuid)

        assert details.address is None

    async def test_returns_only_the_profile_of_the_given_user(self) -> None:
        uow = FakeUnitOfWork()
        user_uuid = uuid4()
        await _register_owner(
            uow, uuid4(), ruc='20600000001', document_number='87654321'
        )
        profile_uuid = await _register_owner(uow, user_uuid)

        details = await GetOwnerProfileUseCase(uow=uow).execute(user_uuid=user_uuid)

        assert (details.uuid, details.user_uuid) == (profile_uuid, user_uuid)

    async def test_rejects_a_user_without_an_owner_profile(self) -> None:
        uow = FakeUnitOfWork()
        await _register_owner(uow, uuid4())

        with pytest.raises(
            OwnerProfileNotFoundError, match='You do not have an owner profile.'
        ):
            await GetOwnerProfileUseCase(uow=uow).execute(user_uuid=uuid4())
