from uuid import UUID

import jwt

from app.owner_profile.domain.exceptions import InvalidSessionTokenError
from app.owner_profile.domain.ports.output.session_token_verifier_port import (
    SessionTokenVerifierPort,
)
from app.owner_profile.infrastructure.security.messages import INVALID_SESSION_TOKEN

REQUIRED_CLAIMS = ['sub', 'iss', 'iat', 'exp']


class JwtSessionTokenVerifier(SessionTokenVerifierPort):
    def __init__(self, public_key: str, algorithm: str, issuer: str) -> None:
        self._public_key = public_key
        # A list with one algorithm: the token's own `alg` is never trusted.
        self._algorithms = [algorithm]
        self._issuer = issuer

    def verify(self, token: str) -> UUID:
        try:
            claims = jwt.decode(
                token,
                self._public_key,
                algorithms=self._algorithms,
                issuer=self._issuer,
                options={'require': REQUIRED_CLAIMS},
            )
            return UUID(claims['sub'])
        except (jwt.InvalidTokenError, ValueError, TypeError) as error:
            raise InvalidSessionTokenError(INVALID_SESSION_TOKEN) from error
