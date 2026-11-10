from typing import Any

from app.owner_profile.infrastructure.api.messages import (
    SIGN_IN_REQUIRED,
    UNEXPECTED_ERROR,
)
from app.owner_profile.infrastructure.api.schemas.api_response import ApiErrorResponse


def example(summary: str, value: dict[str, Any]) -> dict[str, Any]:
    return {'summary': summary, 'value': value}


def success_example(summary: str, data: dict[str, Any]) -> dict[str, Any]:
    value = {'success': True, 'message': '', 'detail': None, 'data': data}
    return example(summary, value)


def error_example(
    summary: str, message: str, detail: list[dict[str, str]] | None = None
) -> dict[str, Any]:
    value = {'success': False, 'message': message, 'detail': detail, 'data': None}
    return example(summary, value)


def json_content(**examples: dict[str, Any]) -> dict[str, Any]:
    return {'application/json': {'examples': examples}}


def error_response(description: str, **examples: dict[str, Any]) -> dict[str, Any]:
    return {
        'model': ApiErrorResponse,
        'description': description,
        'content': json_content(**examples),
    }


SIGN_IN_REQUIRED_RESPONSE = error_response(
    'The session token is missing, malformed, from another issuer or expired.',
    sign_in_required=error_example('No valid session', SIGN_IN_REQUIRED),
)

UNEXPECTED_ERROR_RESPONSE = error_response(
    'An error the service does not control (database, internal).',
    unexpected=error_example('Unexpected error', UNEXPECTED_ERROR),
)
