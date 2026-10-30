from copy import deepcopy
from datetime import datetime
from uuid import UUID

from app.owner_profile.domain.entities.identity_document import DocumentType
from app.owner_profile.domain.entities.owner_profile import OwnerProfile
from app.owner_profile.domain.ports.output.clock_port import ClockPort
from app.owner_profile.domain.ports.output.owner_profile_repository_port import (
    OwnerProfileRepositoryPort,
)
from app.owner_profile.domain.ports.output.unit_of_work_port import UnitOfWorkPort


class FakeOwnerProfileRepository(OwnerProfileRepositoryPort):
    """Stores copies, like a database: a test cannot pass because the stored profile
    and the returned one are the same instance."""

    def __init__(self, profiles: list[OwnerProfile] | None = None) -> None:
        self.profiles = [deepcopy(profile) for profile in profiles or []]

    async def add(self, profile: OwnerProfile) -> None:
        self.profiles.append(deepcopy(profile))

    async def exists_by_user_uuid(self, user_uuid: UUID) -> bool:
        return any(profile.user_uuid == user_uuid for profile in self.profiles)

    async def exists_by_ruc(self, ruc: str) -> bool:
        return any(profile.ruc == ruc for profile in self.profiles)

    async def exists_by_document(
        self, document_type: DocumentType, document_number: str
    ) -> bool:
        return any(
            document.document_type == document_type
            and document.document_number == document_number
            for profile in self.profiles
            for document in profile.identity_documents
        )


class FakeUnitOfWork(UnitOfWorkPort):
    def __init__(self, owner_profiles: list[OwnerProfile] | None = None) -> None:
        self.owner_profiles = FakeOwnerProfileRepository(owner_profiles)
        self.committed = False

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        pass


class FakeClock(ClockPort):
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current
