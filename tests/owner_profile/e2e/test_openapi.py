from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from app.owner_profile.infrastructure.api.schemas.api_response import (
    ApiErrorResponse,
    ApiResponse,
)
from app.owner_profile.infrastructure.api.schemas.owner_profile_schema import (
    GetOwnerProfileData,
    OwnerProfileRequest,
    RegisterOwnerProfileData,
)
from app.owner_profile.main import app

# Public contract: FastAPI docs live at the root, outside the API prefix.
OPENAPI_PATH = '/openapi.json'

# Every published operation (path, method): its request model (if it has a body), its
# success model and every response code of its contract (the tickets' §5). Every one
# needs the session token.
OPERATIONS: dict[tuple[str, str], dict[str, Any]] = {
    ('/api/v1/owner-profiles', 'post'): {
        'request': OwnerProfileRequest,
        'success': ('201', ApiResponse[RegisterOwnerProfileData]),
        'codes': {'201', '401', '409', '422', '500'},
    },
    ('/api/v1/owner-profiles/me', 'get'): {
        'success': ('200', ApiResponse[GetOwnerProfileData]),
        'codes': {'200', '401', '404', '500'},
    },
}
WITH_BODY = [key for key, spec in OPERATIONS.items() if 'request' in spec]


def _id(key: tuple[str, str]) -> str:
    return f'{key[1]} {key[0]}'


@pytest_asyncio.fixture
async def openapi() -> dict[str, Any]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as client:
        return dict((await client.get(OPENAPI_PATH)).json())


def _operation(openapi: dict[str, Any], key: tuple[str, str]) -> dict[str, Any]:
    path, method = key
    return dict(openapi['paths'][path][method])


def _examples(content: dict[str, Any]) -> list[Any]:
    examples = content.get('application/json', {}).get('examples', {})
    return [example['value'] for example in examples.values()]


def _model_of(code: str, spec: dict[str, Any]) -> type[BaseModel]:
    success_code, success_model = spec['success']
    return success_model if code == success_code else ApiErrorResponse


class TestOpenApi:
    async def test_is_titled_with_the_service_name(self, openapi):
        assert openapi['info']['title'] == 'TurfBook Owner Service'

    async def test_no_operation_is_published_without_its_documentation(self, openapi):
        published = {
            (path, method)
            for path, methods in openapi['paths'].items()
            for method in methods
        }

        assert published == set(OPERATIONS)

    @pytest.mark.parametrize('key', OPERATIONS, ids=_id)
    async def test_documents_every_code_of_its_contract(self, openapi, key):
        responses = _operation(openapi, key)['responses']

        assert set(responses) == OPERATIONS[key]['codes']

    @pytest.mark.parametrize('key', OPERATIONS, ids=_id)
    async def test_errors_use_the_error_envelope(self, openapi, key):
        responses = _operation(openapi, key)['responses']

        for code, response in responses.items():
            if code.startswith(('4', '5')):
                schema = response['content']['application/json']['schema']
                assert schema['$ref'].endswith('/ApiErrorResponse'), code

    @pytest.mark.parametrize('key', OPERATIONS, ids=_id)
    async def test_has_a_summary_and_a_description(self, openapi, key):
        operation = _operation(openapi, key)

        assert operation.get('summary')
        assert operation.get('description')

    @pytest.mark.parametrize('key', WITH_BODY, ids=_id)
    async def test_request_examples_are_valid_requests(self, openapi, key):
        content = _operation(openapi, key)['requestBody']['content']

        examples = _examples(content)

        assert examples
        for example in examples:
            OPERATIONS[key]['request'].model_validate(example)

    @pytest.mark.parametrize('key', OPERATIONS, ids=_id)
    async def test_response_examples_match_their_model(self, openapi, key):
        responses = _operation(openapi, key)['responses']

        for code, response in responses.items():
            examples = _examples(response.get('content', {}))
            assert examples, code
            for example in examples:
                _model_of(code, OPERATIONS[key]).model_validate(example)

    @pytest.mark.parametrize('key', OPERATIONS, ids=_id)
    async def test_declares_the_session_token_it_needs(self, openapi, key):
        [requirement] = _operation(openapi, key)['security']
        [scheme_name] = requirement
        scheme = openapi['components']['securitySchemes'][scheme_name]

        assert (scheme['type'], scheme['scheme']) == ('http', 'bearer')
