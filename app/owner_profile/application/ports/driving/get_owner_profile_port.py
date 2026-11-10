from abc import ABC, abstractmethod
from uuid import UUID

from app.owner_profile.application.dtos.outputs import OwnerProfileDetails


class GetOwnerProfilePort(ABC):
    @abstractmethod
    async def execute(self, user_uuid: UUID) -> OwnerProfileDetails:
        """The user's owner profile; raises OwnerProfileNotFoundError when the user
        has none."""
