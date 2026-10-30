from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.owner_profile.application.use_cases.register_owner_profile import (
    RegisterOwnerProfileUseCase,
)
from app.owner_profile.domain.entities.identity_document import DocumentType
from app.owner_profile.domain.entities.owner_profile import OwnerProfile
from app.owner_profile.domain.exceptions import (
    DomainError,
    DuplicateDocumentNumberError,
    DuplicateRucError,
    InvalidAddressError,
    InvalidDocumentNumberError,
    InvalidOwnerProfileError,
    InvalidRucError,
    OwnerProfileAlreadyExistsError,
)
from tests.fakes.owner_profile import FakeClock, FakeUnitOfWork

NOW = datetime(2026, 10, 29, 15, 30, tzinfo=UTC)
USER_UUID = uuid4()
ADDRESS = 'Ayacucho-Huamanga-Ayacucho:Pasaje Los Ángeles Mz 24 Lt A'

INVALID_RUC = 'RUC must have 11 digits and start with 10, 15 or 20.'
INVALID_DNI = 'DNI must have exactly 8 digits.'
INVALID_DOCUMENT_NUMBER = 'Document number must have 1 to 15 letters or digits.'
INVALID_ADDRESS = 'Address must have the format Department-Province-District:Street.'
ADDRESS_TOO_LONG = 'Address must have at most 400 characters.'


def _valid_input(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        'user_uuid': USER_UUID,
        'ruc': '10712345671',
        'document_type': DocumentType.DNI,
        'document_number': '71234567',
        'address': ADDRESS,
    }
    data.update(overrides)
    return data


def _existing_profile(**overrides: Any) -> OwnerProfile:
    """A stored profile that collides with the valid input in nothing but the
    overridden fields."""
    data: dict[str, Any] = {
        'user_uuid': uuid4(),
        'ruc': '20600000001',
        'document_type': DocumentType.PASSPORT,
        'document_number': 'EXISTING01',
        'address': None,
        'now': NOW,
    }
    data.update(overrides)
    return OwnerProfile.register(**data)


def _register(uow: FakeUnitOfWork) -> RegisterOwnerProfileUseCase:
    return RegisterOwnerProfileUseCase(uow=uow, clock=FakeClock(NOW))


def _rule_errors(
    error: pytest.ExceptionInfo[InvalidOwnerProfileError],
) -> list[tuple[type[DomainError], str]]:
    return [(type(rule_error), str(rule_error)) for rule_error in error.value.errors]


async def _assert_rejected(
    uow: FakeUnitOfWork, **overrides: Any
) -> list[tuple[type[DomainError], str]]:
    with pytest.raises(InvalidOwnerProfileError) as error:
        await _register(uow).execute(**_valid_input(**overrides))

    assert uow.owner_profiles.profiles == []
    assert uow.committed is False
    return _rule_errors(error)


class TestRegisterOwnerProfile:
    async def test_registers_the_profile_and_commits(self) -> None:
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(**_valid_input())

        assert uow.owner_profiles.profiles == [profile]
        assert uow.committed is True

    async def test_the_profile_belongs_to_the_given_user(self) -> None:
        user_uuid = uuid4()
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(**_valid_input(user_uuid=user_uuid))

        assert profile.user_uuid == user_uuid

    async def test_keeps_the_ruc_and_the_address_as_sent(self) -> None:
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(**_valid_input())

        assert (profile.ruc, profile.address) == ('10712345671', ADDRESS)

    async def test_keeps_a_street_that_contains_dashes_and_colons(self) -> None:
        address = 'Ayacucho-Huamanga-Ayacucho:Jr. Lima 123-B: 2do piso'
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(**_valid_input(address=address))

        assert profile.address == address

    async def test_registers_a_profile_without_address(self) -> None:
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(**_valid_input(address=None))

        assert profile.address is None
        assert uow.committed is True

    async def test_registers_the_document_as_the_default_one(self) -> None:
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(**_valid_input())

        assert [
            (doc.document_type, doc.document_number, doc.is_default)
            for doc in profile.identity_documents
        ] == [(DocumentType.DNI, '71234567', True)]


class TestRegisterOwnerProfileRuc:
    @pytest.mark.parametrize('ruc', ['10712345671', '15712345671', '20712345671'])
    async def test_accepts_a_ruc_with_an_allowed_prefix(self, ruc: str) -> None:
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(**_valid_input(ruc=ruc))

        assert profile.ruc == ruc

    @pytest.mark.parametrize(
        'ruc',
        [
            pytest.param('1071234567', id='10 digits'),
            pytest.param('107123456712', id='12 digits'),
            pytest.param('30712345671', id='prefix not allowed'),
            pytest.param('1071234567a', id='a letter'),
            pytest.param('', id='empty'),
            pytest.param('10٧١٢٣٤٥٦٧١', id='non-ASCII digits after the prefix'),
        ],
    )
    async def test_rejects_an_invalid_ruc_without_registering(self, ruc: str) -> None:
        errors = await _assert_rejected(FakeUnitOfWork(), ruc=ruc)

        assert errors == [(InvalidRucError, INVALID_RUC)]


class TestRegisterOwnerProfileDocument:
    @pytest.mark.parametrize(
        'document_number',
        [
            pytest.param('1234567', id='7 digits'),
            pytest.param('123456789', id='9 digits'),
            pytest.param('1234567a', id='a letter'),
            pytest.param('', id='empty'),
            pytest.param('٧١٢٣٤٥٦٧', id='non-ASCII digits'),
        ],
    )
    async def test_rejects_a_dni_without_exactly_8_digits(
        self, document_number: str
    ) -> None:
        errors = await _assert_rejected(
            FakeUnitOfWork(),
            document_type=DocumentType.DNI,
            document_number=document_number,
        )

        assert errors == [(InvalidDocumentNumberError, INVALID_DNI)]

    @pytest.mark.parametrize(
        'document_type', [DocumentType.PASSPORT, DocumentType.CARNET_EXTRANJERIA]
    )
    @pytest.mark.parametrize('document_number', ['A', 'AB1234567', 'A' * 15])
    async def test_accepts_other_documents_of_1_to_15_letters_or_digits(
        self, document_type: DocumentType, document_number: str
    ) -> None:
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(
            **_valid_input(document_type=document_type, document_number=document_number)
        )

        assert profile.identity_documents[0].document_number == document_number

    @pytest.mark.parametrize(
        'document_type', [DocumentType.PASSPORT, DocumentType.CARNET_EXTRANJERIA]
    )
    @pytest.mark.parametrize(
        'document_number',
        [
            pytest.param('', id='empty'),
            pytest.param('A' * 16, id='16 characters'),
            pytest.param('AB-123', id='a dash'),
            pytest.param('AB 123', id='a space'),
        ],
    )
    async def test_rejects_other_documents_that_are_not_1_to_15_letters_or_digits(
        self, document_type: DocumentType, document_number: str
    ) -> None:
        errors = await _assert_rejected(
            FakeUnitOfWork(),
            document_type=document_type,
            document_number=document_number,
        )

        assert errors == [(InvalidDocumentNumberError, INVALID_DOCUMENT_NUMBER)]


class TestRegisterOwnerProfileAddress:
    @pytest.mark.parametrize(
        'address',
        [
            pytest.param('Ayacucho-Huamanga-Ayacucho Jr. Lima', id='no colon'),
            pytest.param('Ayacucho-Huamanga:Jr. Lima', id='two parts'),
            pytest.param('Perú-Ayacucho-Huamanga-Ayacucho:Jr. Lima', id='four parts'),
            pytest.param('Ayacucho--Ayacucho:Jr. Lima', id='empty part'),
            pytest.param('Ayacucho-   -Ayacucho:Jr. Lima', id='blank part'),
            pytest.param('Ayacucho-Huamanga-Ayacucho:', id='empty street'),
            pytest.param('Ayacucho-Huamanga-Ayacucho:   ', id='blank street'),
            pytest.param('', id='empty'),
        ],
    )
    async def test_rejects_an_address_without_the_format(self, address: str) -> None:
        errors = await _assert_rejected(FakeUnitOfWork(), address=address)

        assert errors == [(InvalidAddressError, INVALID_ADDRESS)]

    async def test_accepts_an_address_of_400_characters(self) -> None:
        address = 'Ayacucho-Huamanga-Ayacucho:'.ljust(400, 'x')
        uow = FakeUnitOfWork()

        profile = await _register(uow).execute(**_valid_input(address=address))

        assert profile.address == address

    async def test_rejects_an_address_longer_than_400_characters(self) -> None:
        address = 'Ayacucho-Huamanga-Ayacucho:'.ljust(401, 'x')

        errors = await _assert_rejected(FakeUnitOfWork(), address=address)

        assert errors == [(InvalidAddressError, ADDRESS_TOO_LONG)]


class TestRegisterOwnerProfileInvalidFields:
    async def test_reports_every_invalid_field_in_one_error(self) -> None:
        errors = await _assert_rejected(
            FakeUnitOfWork(), ruc='123', document_number='1', address='Ayacucho'
        )

        assert sorted(errors, key=lambda error: error[0].__name__) == [
            (InvalidAddressError, INVALID_ADDRESS),
            (InvalidDocumentNumberError, INVALID_DNI),
            (InvalidRucError, INVALID_RUC),
        ]

    async def test_an_invalid_field_wins_over_an_existing_profile(self) -> None:
        uow = FakeUnitOfWork(owner_profiles=[_existing_profile(user_uuid=USER_UUID)])

        with pytest.raises(InvalidOwnerProfileError):
            await _register(uow).execute(**_valid_input(ruc='123'))

        assert uow.committed is False


class TestRegisterOwnerProfileUniqueness:
    async def test_rejects_a_user_that_already_has_a_profile(self) -> None:
        existing = _existing_profile(user_uuid=USER_UUID)
        uow = FakeUnitOfWork(owner_profiles=[existing])

        with pytest.raises(
            OwnerProfileAlreadyExistsError, match='You already have an owner profile.'
        ):
            await _register(uow).execute(**_valid_input())

        assert uow.owner_profiles.profiles == [existing]
        assert uow.committed is False

    async def test_rejects_a_ruc_registered_by_another_owner(self) -> None:
        existing = _existing_profile(ruc='10712345671')
        uow = FakeUnitOfWork(owner_profiles=[existing])

        with pytest.raises(
            DuplicateRucError, match='This RUC is already registered by another owner.'
        ):
            await _register(uow).execute(**_valid_input(ruc='10712345671'))

        assert uow.owner_profiles.profiles == [existing]
        assert uow.committed is False

    async def test_rejects_a_document_with_the_same_type_and_number(self) -> None:
        existing = _existing_profile(
            document_type=DocumentType.DNI, document_number='71234567'
        )
        uow = FakeUnitOfWork(owner_profiles=[existing])

        with pytest.raises(
            DuplicateDocumentNumberError,
            match='This identity document is already registered.',
        ):
            await _register(uow).execute(
                **_valid_input(
                    document_type=DocumentType.DNI, document_number='71234567'
                )
            )

        assert uow.owner_profiles.profiles == [existing]
        assert uow.committed is False

    async def test_accepts_a_number_registered_with_another_document_type(
        self,
    ) -> None:
        uow = FakeUnitOfWork(
            owner_profiles=[
                _existing_profile(
                    document_type=DocumentType.PASSPORT, document_number='71234567'
                )
            ]
        )

        await _register(uow).execute(
            **_valid_input(document_type=DocumentType.DNI, document_number='71234567')
        )

        assert uow.committed is True

    async def test_an_existing_profile_is_reported_before_a_duplicate_ruc(
        self,
    ) -> None:
        uow = FakeUnitOfWork(
            owner_profiles=[
                _existing_profile(user_uuid=USER_UUID),
                _existing_profile(ruc='10712345671'),
            ]
        )

        with pytest.raises(OwnerProfileAlreadyExistsError):
            await _register(uow).execute(**_valid_input(ruc='10712345671'))

    async def test_a_duplicate_ruc_is_reported_before_a_duplicate_document(
        self,
    ) -> None:
        uow = FakeUnitOfWork(
            owner_profiles=[
                _existing_profile(ruc='10712345671'),
                _existing_profile(
                    document_type=DocumentType.DNI, document_number='71234567'
                ),
            ]
        )

        with pytest.raises(DuplicateRucError):
            await _register(uow).execute(**_valid_input())
