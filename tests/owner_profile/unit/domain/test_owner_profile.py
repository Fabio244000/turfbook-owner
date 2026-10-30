from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.owner_profile.domain.entities.identity_document import DocumentType
from app.owner_profile.domain.entities.owner_profile import OwnerProfile
from app.owner_profile.domain.exceptions import (
    InvalidAddressError,
    InvalidDocumentNumberError,
    InvalidOwnerProfileError,
    InvalidRucError,
)

NOW = datetime(2026, 10, 29, 15, 30, tzinfo=UTC)


def _register(**overrides):
    data = {
        'user_uuid': uuid4(),
        'ruc': '10712345671',
        'document_type': DocumentType.DNI,
        'document_number': '71234567',
        'address': 'Ayacucho-Huamanga-Ayacucho:Pasaje Los Ángeles Mz 24 Lt A',
        'now': NOW,
    }
    data.update(overrides)
    return OwnerProfile.register(**data)


class TestOwnerProfileRegister:
    def test_builds_a_profile_whose_only_document_is_the_default_one(self):
        user_uuid = uuid4()

        profile = _register(user_uuid=user_uuid)

        assert profile.user_uuid == user_uuid
        assert [
            (doc.document_type, doc.document_number, doc.is_default)
            for doc in profile.identity_documents
        ] == [(DocumentType.DNI, '71234567', True)]

    def test_reports_every_invalid_field_in_one_error(self):
        with pytest.raises(InvalidOwnerProfileError) as error:
            _register(ruc='123', document_number='1', address='Ayacucho')

        assert {type(rule_error) for rule_error in error.value.errors} == {
            InvalidRucError,
            InvalidDocumentNumberError,
            InvalidAddressError,
        }
