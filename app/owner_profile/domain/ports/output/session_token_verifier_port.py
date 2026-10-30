from abc import ABC, abstractmethod
from uuid import UUID


class SessionTokenVerifierPort(ABC):
    @abstractmethod
    def verify(self, token: str) -> UUID:
        """The user the token belongs to; raises InvalidSessionTokenError otherwise."""
