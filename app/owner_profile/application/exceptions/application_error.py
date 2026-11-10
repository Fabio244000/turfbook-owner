from app.owner_profile.application.messages import OWNER_PROFILE_NOT_FOUND


class ApplicationError(Exception):
    """What a use case tells its caller when an operation fails; the caller (the API,
    a queue consumer) presents it to its client."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class OwnerProfileNotFoundError(ApplicationError):
    def __init__(self) -> None:
        super().__init__(OWNER_PROFILE_NOT_FOUND)
