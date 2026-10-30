from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.owner_profile.application.use_cases.register_owner_profile import (
    RegisterOwnerProfileUseCase,
)
from app.owner_profile.domain.exceptions import InvalidSessionTokenError
from app.owner_profile.domain.ports.input.register_owner_profile_port import (
    RegisterOwnerProfilePort,
)
from app.owner_profile.domain.ports.output.clock_port import ClockPort
from app.owner_profile.domain.ports.output.session_token_verifier_port import (
    SessionTokenVerifierPort,
)
from app.owner_profile.domain.ports.output.unit_of_work_port import UnitOfWorkPort
from app.owner_profile.infrastructure.api.messages import SIGN_IN_REQUIRED
from app.owner_profile.infrastructure.clock.system_clock import SystemClock
from app.owner_profile.infrastructure.database.session import async_session
from app.owner_profile.infrastructure.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.owner_profile.infrastructure.security.jwt_session_token_verifier import (
    JwtSessionTokenVerifier,
)
from config.settings import settings

# auto_error=False: a missing header raises our own error, so the 401 has the envelope.
_bearer = HTTPBearer(auto_error=False)


def get_unit_of_work() -> UnitOfWorkPort:
    return SqlAlchemyUnitOfWork(async_session)


def get_clock() -> ClockPort:
    return SystemClock()


def get_session_token_verifier() -> SessionTokenVerifierPort:
    return JwtSessionTokenVerifier(
        public_key=settings.jwt_public_key,
        algorithm=settings.jwt_algorithm,
        issuer=settings.jwt_issuer,
    )


def get_current_user_uuid(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    verifier: SessionTokenVerifierPort = Depends(get_session_token_verifier),
) -> UUID:
    """The authenticated user. Runs before the body is validated, so a missing or
    invalid token is answered before any data error."""
    if credentials is None:
        raise InvalidSessionTokenError(SIGN_IN_REQUIRED)
    return verifier.verify(credentials.credentials)


def get_register_owner_profile_use_case(
    uow: UnitOfWorkPort = Depends(get_unit_of_work),
    clock: ClockPort = Depends(get_clock),
) -> RegisterOwnerProfilePort:
    return RegisterOwnerProfileUseCase(uow=uow, clock=clock)
