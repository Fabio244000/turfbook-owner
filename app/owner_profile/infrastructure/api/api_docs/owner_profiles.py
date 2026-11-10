from typing import Any

from app.owner_profile.application.messages import (
    DUPLICATE_DOCUMENT,
    DUPLICATE_RUC,
    OWNER_PROFILE_NOT_FOUND,
    PROFILE_ALREADY_EXISTS,
)
from app.owner_profile.domain.messages import INVALID_ADDRESS, INVALID_RUC
from app.owner_profile.infrastructure.api.api_docs.examples import (
    SIGN_IN_REQUIRED_RESPONSE,
    UNEXPECTED_ERROR_RESPONSE,
    error_example,
    error_response,
    example,
    json_content,
    success_example,
)
from app.owner_profile.infrastructure.api.messages import (
    FIELD_LABELS,
    FIELD_REQUIRED,
    INVALID_DATA,
    INVALID_JSON,
)

_ROSA_PROFILE: dict[str, Any] = {
    'uuid': '5d2b7c1e-0f3a-4e8b-9c61-2a7f4e9d1b03',
    'user_uuid': 'a3f1c2e8-9b44-4d7a-8e21-77d0c5b9e1f2',
    'ruc': '10712345671',
    'identity_documents': [
        {'document_type': 'DNI', 'document_number': '71234567', 'is_default': True}
    ],
    'address': 'Ayacucho-Huamanga-Ayacucho:Pasaje Los Ángeles Mz 24 Lt A',
    'created_at': '2026-10-29T15:30:00Z',
}

REGISTER_OWNER_PROFILE_REQUEST_EXAMPLES: dict[str, Any] = {
    'with_address': example(
        'With address',
        {
            'ruc': _ROSA_PROFILE['ruc'],
            'identity_document': {
                'document_type': 'DNI',
                'document_number': '71234567',
            },
            'address': _ROSA_PROFILE['address'],
        },
    ),
    'without_address': example(
        'Without address',
        {
            'ruc': '20600000001',
            'identity_document': {
                'document_type': 'PASSPORT',
                'document_number': 'AB1234567',
            },
        },
    ),
}


def _required(field: str) -> str:
    return FIELD_REQUIRED.format(field=FIELD_LABELS[field])


REGISTER_OWNER_PROFILE_DOCS: dict[str, Any] = {
    'summary': 'Register my owner profile',
    'responses': {
        201: {
            'description': 'The profile is registered; its document is the default '
            'one. `address` is null when it was not sent.',
            'content': json_content(
                registered=success_example('Registered', _ROSA_PROFILE),
            ),
        },
        401: SIGN_IN_REQUIRED_RESPONSE,
        409: error_response(
            'The user already has a profile, or the RUC or the document is taken.',
            profile_exists=error_example(
                'Profile already exists', PROFILE_ALREADY_EXISTS
            ),
            duplicate_ruc=error_example('RUC taken', DUPLICATE_RUC),
            duplicate_document=error_example('Document taken', DUPLICATE_DOCUMENT),
        ),
        422: error_response(
            'The body is not JSON, or a field is missing or breaks its rule.',
            invalid_ruc=error_example('Invalid RUC', INVALID_RUC),
            missing_field=error_example('Missing RUC', _required('ruc')),
            several_fields=error_example(
                'Several invalid fields',
                INVALID_DATA,
                [
                    {'field': 'ruc', 'error': INVALID_RUC},
                    {'field': 'address', 'error': INVALID_ADDRESS},
                ],
            ),
            not_json=error_example('A body that is not JSON', INVALID_JSON),
        ),
        500: UNEXPECTED_ERROR_RESPONSE,
    },
}

GET_OWNER_PROFILE_DOCS: dict[str, Any] = {
    'summary': 'Get my owner profile',
    'responses': {
        200: {
            'description': 'The user is an owner: their profile. `address` is null '
            'when it was not registered.',
            'content': json_content(
                owner=success_example('Owner profile', _ROSA_PROFILE),
            ),
        },
        401: SIGN_IN_REQUIRED_RESPONSE,
        404: error_response(
            'The user has no owner profile: they are a player.',
            not_an_owner=error_example('No owner profile', OWNER_PROFILE_NOT_FOUND),
        ),
        500: UNEXPECTED_ERROR_RESPONSE,
    },
}
