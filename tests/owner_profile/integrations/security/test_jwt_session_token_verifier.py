import hashlib
import hmac
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.utils import base64url_encode

from app.owner_profile.domain.exceptions import InvalidSessionTokenError
from app.owner_profile.infrastructure.security.jwt_session_token_verifier import (
    JwtSessionTokenVerifier,
)

ISSUER = 'turfbook-identity'


def _key_pair() -> tuple[str, str]:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    public_pem = (
        key.public_key()
        .public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode()
    )
    return private_pem, public_pem


PRIVATE_KEY, PUBLIC_KEY = _key_pair()
OTHER_PRIVATE_KEY, _ = _key_pair()


def _claims(**overrides: Any) -> dict[str, Any]:
    now = datetime.now(UTC)
    claims: dict[str, Any] = {
        'sub': str(uuid4()),
        'iss': ISSUER,
        'iat': now,
        'exp': now + timedelta(minutes=15),
    }
    claims.update(overrides)
    return {key: value for key, value in claims.items() if value is not None}


def _token(
    claims: dict[str, Any], key: str = PRIVATE_KEY, algorithm: str = 'RS256'
) -> str:
    return jwt.encode(claims, key, algorithm=algorithm)


def _verifier() -> JwtSessionTokenVerifier:
    return JwtSessionTokenVerifier(
        public_key=PUBLIC_KEY, algorithm='RS256', issuer=ISSUER
    )


class TestJwtSessionTokenVerifier:
    def test_returns_the_user_of_a_valid_token(self) -> None:
        claims = _claims()

        user_uuid = _verifier().verify(_token(claims))

        assert str(user_uuid) == claims['sub']

    @pytest.mark.parametrize(
        'token',
        [
            pytest.param(
                _token(_claims(), key=OTHER_PRIVATE_KEY), id='signed with another key'
            ),
            pytest.param(
                _token(_claims(exp=datetime.now(UTC) - timedelta(seconds=1))),
                id='expired',
            ),
            pytest.param(_token(_claims(iss='someone-else')), id='another issuer'),
            pytest.param(_token(_claims(sub=None)), id='without sub'),
            pytest.param(_token(_claims(iss=None)), id='without iss'),
            pytest.param(_token(_claims(iat=None)), id='without iat'),
            pytest.param(_token(_claims(exp=None)), id='without exp'),
            pytest.param(_token(_claims(sub='not-a-uuid')), id='sub is not a uuid'),
            pytest.param(_token(_claims(), key='', algorithm='none'), id='alg none'),
            pytest.param('not.a.token', id='garbage'),
            pytest.param('', id='empty'),
        ],
    )
    def test_rejects_an_invalid_token(self, token: str) -> None:
        with pytest.raises(InvalidSessionTokenError):
            _verifier().verify(token)

    def test_rejects_a_token_signed_with_hs256_using_the_public_key(self) -> None:
        # Algorithm confusion: the public key used as an HMAC secret. PyJWT refuses to
        # build such a token, so it is signed by hand.
        now = int(datetime.now(UTC).timestamp())
        claims = {'sub': str(uuid4()), 'iss': ISSUER, 'iat': now, 'exp': now + 900}
        signing_input = b'.'.join(
            base64url_encode(json.dumps(part).encode())
            for part in ({'alg': 'HS256', 'typ': 'JWT'}, claims)
        )
        signature = hmac.new(PUBLIC_KEY.encode(), signing_input, hashlib.sha256)
        token = (signing_input + b'.' + base64url_encode(signature.digest())).decode()

        with pytest.raises(InvalidSessionTokenError):
            _verifier().verify(token)
