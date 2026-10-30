from collections.abc import AsyncGenerator, Callable, Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
import pytest_asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.owner_profile.infrastructure.api.dependencies import (
    get_session_token_verifier,
    get_unit_of_work,
)
from app.owner_profile.infrastructure.database.unit_of_work import (
    SqlAlchemyUnitOfWork,
)
from app.owner_profile.infrastructure.security.jwt_session_token_verifier import (
    JwtSessionTokenVerifier,
)
from app.owner_profile.main import app

# Public contract: written literally so an accidental prefix/version change fails here.
OWNER_PROFILES_PATH = '/api/v1/owner-profiles'

# The test plays identity: it signs tokens with this key and owner verifies them.
_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
PRIVATE_KEY = _KEY.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
PUBLIC_KEY = (
    _KEY.public_key()
    .public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    .decode()
)


def session_token(user_uuid: UUID) -> str:
    now = datetime.now(UTC)
    claims = {
        'sub': str(user_uuid),
        'iss': 'turfbook-identity',
        'iat': now,
        'exp': now + timedelta(minutes=15),
    }
    return jwt.encode(claims, PRIVATE_KEY, algorithm='RS256')


def auth(user_uuid: UUID) -> dict[str, str]:
    return {'Authorization': f'Bearer {session_token(user_uuid)}'}


def valid_payload(**overrides: Any) -> dict[str, Any]:
    """A valid request whose RUC and document collide with no existing row."""
    data: dict[str, Any] = {
        'ruc': f'10{uuid4().int % 10**9:09d}',
        'identity_document': {
            'document_type': 'DNI',
            'document_number': f'{uuid4().int % 10**8:08d}',
        },
        'address': 'Ayacucho-Huamanga-Ayacucho:Pasaje Los Ángeles Mz 24 Lt A',
    }
    data.update(overrides)
    return data


@pytest.fixture
def make_client(
    session_factory: async_sessionmaker[AsyncSession],
) -> Generator[Callable[..., AsyncClient], None, None]:
    def _make_client(raise_app_exceptions: bool = True) -> AsyncClient:
        transport = ASGITransport(app=app, raise_app_exceptions=raise_app_exceptions)
        return AsyncClient(transport=transport, base_url='http://test')

    app.dependency_overrides[get_unit_of_work] = lambda: SqlAlchemyUnitOfWork(
        session_factory
    )
    app.dependency_overrides[get_session_token_verifier] = lambda: (
        JwtSessionTokenVerifier(
            public_key=PUBLIC_KEY, algorithm='RS256', issuer='turfbook-identity'
        )
    )
    yield _make_client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(
    make_client: Callable[..., AsyncClient],
) -> AsyncGenerator[AsyncClient, None]:
    async with make_client() as client:
        yield client
