from uuid import uuid4

from app.owner_profile.infrastructure.api.dependencies import get_clock
from app.owner_profile.main import app
from tests.owner_profile.e2e.conftest import OWNER_PROFILES_PATH, auth, valid_payload

SIGN_IN_REQUIRED = 'You must sign in to continue.'


def _error(message, detail=None):
    return {'success': False, 'message': message, 'data': None, 'detail': detail}


class TestRegisterOwnerProfile:
    async def test_returns_201_with_the_profile_of_the_token_user(self, client):
        user_uuid = uuid4()
        payload = valid_payload(user_uuid=str(uuid4()))  # outside the contract: ignored

        response = await client.post(
            OWNER_PROFILES_PATH, json=payload, headers=auth(user_uuid)
        )

        assert response.status_code == 201
        body = response.json()
        assert (body['success'], body['message'], body['detail']) == (True, '', None)
        data = body['data']
        assert data['user_uuid'] == str(user_uuid)
        assert data['ruc'] == payload['ruc']
        assert data['address'] == payload['address']
        assert data['identity_documents'] == [
            {**payload['identity_document'], 'is_default': True}
        ]
        assert set(data) == {
            'uuid',
            'user_uuid',
            'ruc',
            'identity_documents',
            'address',
            'created_at',
        }

    async def test_returns_409_when_the_user_already_has_a_profile(self, client):
        user_uuid = uuid4()
        await client.post(
            OWNER_PROFILES_PATH, json=valid_payload(), headers=auth(user_uuid)
        )

        response = await client.post(
            OWNER_PROFILES_PATH, json=valid_payload(), headers=auth(user_uuid)
        )

        assert response.status_code == 409
        assert response.json() == _error('You already have an owner profile.')


class TestRegisterOwnerProfileAuthentication:
    async def test_returns_401_without_a_token(self, client):
        response = await client.post(OWNER_PROFILES_PATH, json=valid_payload())

        assert response.status_code == 401
        assert response.json() == _error(SIGN_IN_REQUIRED)

    async def test_returns_401_with_an_invalid_token(self, client):
        response = await client.post(
            OWNER_PROFILES_PATH,
            json=valid_payload(),
            headers={'Authorization': 'Bearer not.a.token'},
        )

        assert response.status_code == 401
        assert response.json() == _error(SIGN_IN_REQUIRED)

    async def test_the_token_is_checked_before_the_data(self, client):
        response = await client.post(OWNER_PROFILES_PATH, json={'ruc': 123})

        assert response.status_code == 401

    async def test_a_body_that_is_not_json_is_rejected_before_the_token(self, client):
        response = await client.post(
            OWNER_PROFILES_PATH,
            content='{"ruc": ',
            headers={'Content-Type': 'application/json'},
        )

        assert response.status_code == 422
        assert response.json() == _error('The request body is not valid JSON.')


class TestRegisterOwnerProfileInvalidData:
    async def test_one_invalid_field_answers_its_message_without_detail(self, client):
        response = await client.post(
            OWNER_PROFILES_PATH, json=valid_payload(ruc='123'), headers=auth(uuid4())
        )

        assert response.status_code == 422
        assert response.json() == _error(
            'RUC must have 11 digits and start with 10, 15 or 20.'
        )

    async def test_several_invalid_fields_are_listed_in_detail(self, client):
        payload = valid_payload(
            ruc='123',
            identity_document={'document_type': 'DNI', 'document_number': '1'},
            address='Ayacucho',
        )

        response = await client.post(
            OWNER_PROFILES_PATH, json=payload, headers=auth(uuid4())
        )

        assert response.status_code == 422
        body = response.json()
        assert body['message'] == 'There were problems with the submitted data.'
        assert sorted(body['detail'], key=lambda item: item['field']) == [
            {
                'field': 'address',
                'error': 'Address must have the format Department-Province-District:Street.',
            },
            {
                'field': 'identity_document.document_number',
                'error': 'DNI must have exactly 8 digits.',
            },
            {
                'field': 'ruc',
                'error': 'RUC must have 11 digits and start with 10, 15 or 20.',
            },
        ]

    async def test_a_missing_field_answers_the_api_text(self, client):
        payload = valid_payload()
        del payload['ruc']

        response = await client.post(
            OWNER_PROFILES_PATH, json=payload, headers=auth(uuid4())
        )

        assert response.status_code == 422
        assert response.json() == _error('RUC is required.')

    async def test_an_unsupported_document_type_answers_the_api_text(self, client):
        payload = valid_payload(
            identity_document={'document_type': 'RUC', 'document_number': '1'}
        )

        response = await client.post(
            OWNER_PROFILES_PATH, json=payload, headers=auth(uuid4())
        )

        assert response.status_code == 422
        assert response.json() == _error(
            'Document type must be DNI, PASSPORT or CARNET_EXTRANJERIA.'
        )

    async def test_structure_errors_are_listed_with_nested_paths(self, client):
        payload = valid_payload(ruc=12345678901, identity_document={})

        response = await client.post(
            OWNER_PROFILES_PATH, json=payload, headers=auth(uuid4())
        )

        assert response.status_code == 422
        body = response.json()
        assert body['message'] == 'There were problems with the submitted data.'
        assert sorted(body['detail'], key=lambda item: item['field']) == [
            {
                'field': 'identity_document.document_number',
                'error': 'Document number is required.',
            },
            {
                'field': 'identity_document.document_type',
                'error': 'Document type is required.',
            },
            {'field': 'ruc', 'error': 'RUC has an invalid value.'},
        ]
        assert 'input' not in response.text


class TestRegisterOwnerProfileUnexpectedError:
    async def test_returns_500_without_internal_detail(self, make_client):
        def broken_clock():
            raise RuntimeError('database password is p4ss')

        app.dependency_overrides[get_clock] = broken_clock
        async with make_client(raise_app_exceptions=False) as client:
            response = await client.post(
                OWNER_PROFILES_PATH, json=valid_payload(), headers=auth(uuid4())
            )

        assert response.status_code == 500
        assert response.json() == _error(
            'An unexpected error occurred. Please try again later.'
        )
        assert 'p4ss' not in response.text
