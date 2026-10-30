from dataclasses import replace
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.owner_profile.domain.exceptions import (
    DuplicateDocumentNumberError,
    DuplicateRucError,
    OwnerProfileAlreadyExistsError,
)
from app.owner_profile.infrastructure.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
)


class TestSqlAlchemyUnitOfWork:
    async def test_commit_saves_the_work(
        self, session_factory, new_owner_profile, stored_owner_profile
    ):
        profile = new_owner_profile()

        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await uow.owner_profiles.add(profile)
            await uow.commit()

        assert await stored_owner_profile(profile.uuid) is not None

    async def test_leaving_without_commit_discards_the_work(
        self, session_factory, new_owner_profile, stored_owner_profile
    ):
        profile = new_owner_profile()

        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await uow.owner_profiles.add(profile)
            await uow.owner_profiles.exists_by_ruc(profile.ruc)  # sends the INSERT

        assert await stored_owner_profile(profile.uuid) is None

    async def test_an_error_inside_the_block_discards_the_work(
        self, session_factory, new_owner_profile, stored_owner_profile
    ):
        profile = new_owner_profile()

        with pytest.raises(RuntimeError):
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                await uow.owner_profiles.add(profile)
                await uow.owner_profiles.exists_by_ruc(profile.ruc)  # sends the INSERT
                raise RuntimeError('fails after writing')

        assert await stored_owner_profile(profile.uuid) is None


class TestSqlAlchemyUnitOfWorkConcurrentDuplicates:
    """Duplicates the use case could not see: the database's unique constraints
    find them on commit, and the unit of work translates each one."""

    async def test_a_second_profile_of_the_same_user_raises_already_exists(
        self, session_factory, new_owner_profile, insert_owner_profile
    ):
        existing = new_owner_profile()
        await insert_owner_profile(existing)
        duplicate = new_owner_profile(user_uuid=existing.user_uuid)

        with pytest.raises(OwnerProfileAlreadyExistsError):
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                await uow.owner_profiles.add(duplicate)
                await uow.commit()

    async def test_a_registered_ruc_raises_duplicate_ruc(
        self, session_factory, new_owner_profile, insert_owner_profile
    ):
        existing = new_owner_profile()
        await insert_owner_profile(existing)
        duplicate = new_owner_profile(ruc=existing.ruc)

        with pytest.raises(DuplicateRucError):
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                await uow.owner_profiles.add(duplicate)
                await uow.commit()

    async def test_a_registered_document_raises_duplicate_document_and_keeps_no_profile(
        self,
        session_factory,
        new_owner_profile,
        insert_owner_profile,
        stored_owner_profile,
    ):
        existing = new_owner_profile()
        await insert_owner_profile(existing)
        duplicate = new_owner_profile(
            document_number=existing.identity_documents[0].document_number
        )

        with pytest.raises(DuplicateDocumentNumberError):
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                await uow.owner_profiles.add(duplicate)
                await uow.commit()

        assert await stored_owner_profile(duplicate.uuid) is None

    async def test_a_violation_without_business_meaning_is_not_translated(
        self, session_factory, new_owner_profile
    ):
        profile = new_owner_profile()
        document = profile.identity_documents[0]
        # A new row (own uuid, unique number) whose only fault is being a second
        # default document of the same owner.
        second_default = replace(
            document, uuid=uuid4(), document_number=f'{uuid4().int % 10**8:08d}'
        )
        profile.identity_documents.append(second_default)

        with pytest.raises(IntegrityError):
            async with SqlAlchemyUnitOfWork(session_factory) as uow:
                await uow.owner_profiles.add(profile)
                await uow.commit()
