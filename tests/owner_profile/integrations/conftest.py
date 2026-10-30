from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.owner_profile.domain.entities.identity_document import DocumentType
from app.owner_profile.domain.entities.owner_profile import OwnerProfile

StoredOwnerProfile = tuple[Any, ...] | None

REGISTERED_AT = datetime(2026, 10, 29, 15, 30, tzinfo=UTC)


def _unique_ruc() -> str:
    return f'20{uuid4().int % 10**9:09d}'


def _unique_dni() -> str:
    return f'{uuid4().int % 10**8:08d}'


@pytest.fixture
def new_owner_profile() -> Callable[..., OwnerProfile]:
    """Builds a valid OwnerProfile whose unique fields collide with no existing row."""

    def _new_owner_profile(**overrides: Any) -> OwnerProfile:
        data: dict[str, Any] = {
            'user_uuid': uuid4(),
            'ruc': _unique_ruc(),
            'document_type': DocumentType.DNI,
            'document_number': _unique_dni(),
            'address': 'Ayacucho-Huamanga-Ayacucho:Jr. Lima 123',
            'now': REGISTERED_AT,
        }
        data.update(overrides)
        return OwnerProfile.register(**data)

    return _new_owner_profile


@pytest.fixture
def insert_owner_profile(
    connection: AsyncConnection,
) -> Callable[[OwnerProfile], Awaitable[None]]:
    async def _insert_owner_profile(profile: OwnerProfile) -> None:
        await connection.execute(
            text(
                'INSERT INTO owner_profiles (uuid, user_uuid, ruc, address,'
                ' created_at, updated_at)'
                ' VALUES (:uuid, :user_uuid, :ruc, :address, :created_at, :updated_at)'
            ),
            {
                'uuid': profile.uuid,
                'user_uuid': profile.user_uuid,
                'ruc': profile.ruc,
                'address': profile.address,
                'created_at': profile.created_at,
                'updated_at': profile.updated_at,
            },
        )
        for document in profile.identity_documents:
            await connection.execute(
                text(
                    'INSERT INTO identity_documents (uuid, owner_profile_uuid,'
                    ' document_type, document_number, is_default, created_at)'
                    ' VALUES (:uuid, :owner_profile_uuid, :document_type,'
                    ' :document_number, :is_default, :created_at)'
                ),
                {
                    'uuid': document.uuid,
                    'owner_profile_uuid': profile.uuid,
                    'document_type': document.document_type.value,
                    'document_number': document.document_number,
                    'is_default': document.is_default,
                    'created_at': document.created_at,
                },
            )

    return _insert_owner_profile


@pytest.fixture
def stored_owner_profile(
    connection: AsyncConnection,
) -> Callable[[UUID], Awaitable[StoredOwnerProfile]]:
    async def _stored_owner_profile(uuid: UUID) -> StoredOwnerProfile:
        result = await connection.execute(
            text(
                'SELECT user_uuid, ruc, address, created_at, updated_at'
                ' FROM owner_profiles WHERE uuid = :uuid'
            ),
            {'uuid': uuid},
        )
        row = result.one_or_none()
        return tuple(row) if row else None

    return _stored_owner_profile


@pytest.fixture
def stored_documents(
    connection: AsyncConnection,
) -> Callable[[UUID], Awaitable[list[tuple[Any, ...]]]]:
    async def _stored_documents(owner_profile_uuid: UUID) -> list[tuple[Any, ...]]:
        result = await connection.execute(
            text(
                'SELECT document_type, document_number, is_default, created_at'
                ' FROM identity_documents WHERE owner_profile_uuid = :uuid'
            ),
            {'uuid': owner_profile_uuid},
        )
        return [tuple(row) for row in result]

    return _stored_documents
