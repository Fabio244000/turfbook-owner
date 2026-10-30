from app.owner_profile.domain.entities.identity_document import DocumentType
from app.owner_profile.infrastructure.database.repositories.owner_profile_repository import (
    OwnerProfileRepository,
)
from tests.owner_profile.integrations.conftest import REGISTERED_AT


class TestOwnerProfileRepositoryAdd:
    async def test_adds_the_profile(
        self, session, new_owner_profile, stored_owner_profile
    ):
        profile = new_owner_profile()

        await OwnerProfileRepository(session).add(profile)
        await session.commit()

        assert await stored_owner_profile(profile.uuid) == (
            profile.user_uuid,
            profile.ruc,
            profile.address,
            REGISTERED_AT,
            REGISTERED_AT,
        )

    async def test_adds_the_profile_together_with_its_documents(
        self, session, new_owner_profile, stored_documents
    ):
        profile = new_owner_profile()

        await OwnerProfileRepository(session).add(profile)
        await session.commit()

        document = profile.identity_documents[0]
        assert await stored_documents(profile.uuid) == [
            ('DNI', document.document_number, True, REGISTERED_AT)
        ]

    async def test_adds_a_profile_without_address(
        self, session, new_owner_profile, stored_owner_profile
    ):
        profile = new_owner_profile(address=None)

        await OwnerProfileRepository(session).add(profile)
        await session.commit()

        stored = await stored_owner_profile(profile.uuid)
        assert stored is not None
        assert stored[2] is None


class TestOwnerProfileRepositoryExists:
    async def test_finds_a_user_that_has_a_profile(
        self, session, new_owner_profile, insert_owner_profile
    ):
        profile = new_owner_profile()
        await insert_owner_profile(profile)

        exists = await OwnerProfileRepository(session).exists_by_user_uuid(
            profile.user_uuid
        )

        assert exists is True

    async def test_does_not_find_a_user_without_profile(
        self, session, new_owner_profile
    ):
        exists = await OwnerProfileRepository(session).exists_by_user_uuid(
            new_owner_profile().user_uuid
        )

        assert exists is False

    async def test_finds_a_registered_ruc(
        self, session, new_owner_profile, insert_owner_profile
    ):
        profile = new_owner_profile()
        await insert_owner_profile(profile)

        exists = await OwnerProfileRepository(session).exists_by_ruc(profile.ruc)

        assert exists is True

    async def test_does_not_find_a_ruc_nobody_has(self, session, new_owner_profile):
        exists = await OwnerProfileRepository(session).exists_by_ruc(
            new_owner_profile().ruc
        )

        assert exists is False

    async def test_finds_a_document_with_the_same_type_and_number(
        self, session, new_owner_profile, insert_owner_profile
    ):
        profile = new_owner_profile()
        await insert_owner_profile(profile)
        document = profile.identity_documents[0]

        exists = await OwnerProfileRepository(session).exists_by_document(
            DocumentType.DNI, document.document_number
        )

        assert exists is True

    async def test_does_not_find_the_same_number_with_another_type(
        self, session, new_owner_profile, insert_owner_profile
    ):
        profile = new_owner_profile()
        await insert_owner_profile(profile)
        document = profile.identity_documents[0]

        exists = await OwnerProfileRepository(session).exists_by_document(
            DocumentType.PASSPORT, document.document_number
        )

        assert exists is False
