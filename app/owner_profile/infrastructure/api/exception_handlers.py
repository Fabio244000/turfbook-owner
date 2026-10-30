import logging
from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.owner_profile.domain.exceptions import (
    DomainError,
    DuplicateDocumentNumberError,
    DuplicateRucError,
    InvalidAddressError,
    InvalidDocumentNumberError,
    InvalidOwnerProfileError,
    InvalidRucError,
    InvalidSessionTokenError,
    OwnerProfileAlreadyExistsError,
)
from app.owner_profile.infrastructure.api.messages import (
    DOCUMENT_TYPE_NOT_ALLOWED,
    FIELD_INVALID,
    FIELD_INVALID_VALUE,
    FIELD_LABELS,
    FIELD_REQUIRED,
    INVALID_DATA,
    INVALID_JSON,
    SIGN_IN_REQUIRED,
    UNEXPECTED_ERROR,
    UNEXPECTED_ERROR_LOG,
)
from app.owner_profile.infrastructure.api.schemas.api_response import (
    ApiResponse,
    FieldError,
)

logger = logging.getLogger(__name__)

STATUS_MAP: dict[type[DomainError], int] = {
    InvalidOwnerProfileError: 422,
    InvalidSessionTokenError: 401,
    OwnerProfileAlreadyExistsError: 409,
    DuplicateRucError: 409,
    DuplicateDocumentNumberError: 409,
}

# The domain does not know the JSON: the API says which field each rule error is about.
FIELD_MAP: dict[type[DomainError], str] = {
    InvalidRucError: 'ruc',
    InvalidDocumentNumberError: 'identity_document.document_number',
    InvalidAddressError: 'address',
}

# Pydantic texts are technical and may echo the input, so the API writes its own.
STRUCTURE_TEXTS = {
    'missing': FIELD_REQUIRED,
    'string_type': FIELD_INVALID_VALUE,
    'model_type': FIELD_INVALID_VALUE,
    'model_attributes_type': FIELD_INVALID_VALUE,
}
ENUM_TEXTS = {'identity_document.document_type': DOCUMENT_TYPE_NOT_ALLOWED}


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status_code = STATUS_MAP.get(type(exc)) if isinstance(exc, DomainError) else None
    if status_code is None:
        return await unexpected_error_handler(request, exc)
    if isinstance(exc, InvalidOwnerProfileError):
        return _invalid_fields(
            [FieldError(field=FIELD_MAP[type(e)], error=str(e)) for e in exc.errors]
        )
    # One text for any token failure: the client never learns why it failed.
    message = (
        SIGN_IN_REQUIRED if isinstance(exc, InvalidSessionTokenError) else str(exc)
    )
    return _response(status_code, message)


async def request_validation_handler(request: Request, exc: Exception) -> JSONResponse:
    errors = list(exc.errors()) if isinstance(exc, RequestValidationError) else []
    if any(error['type'] == 'json_invalid' for error in errors):
        return _response(422, INVALID_JSON)
    return _invalid_fields([_structure_error(error) for error in errors])


async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(UNEXPECTED_ERROR_LOG, exc_info=exc)
    return _response(500, UNEXPECTED_ERROR)


def _structure_error(error: dict[str, Any]) -> FieldError:
    """A Pydantic error with the API's own text: never Pydantic's text or input."""
    # loc starts with where the value came from ('body'), which is not part of the
    # field's name in the contract.
    field = '.'.join(str(part) for part in error['loc'][1:])
    label = FIELD_LABELS.get(field, field)
    if error['type'] == 'enum' and field in ENUM_TEXTS:
        return FieldError(field=field, error=ENUM_TEXTS[field])
    template = STRUCTURE_TEXTS.get(error['type'], FIELD_INVALID)
    return FieldError(field=field, error=template.format(field=label))


def _invalid_fields(errors: list[FieldError]) -> JSONResponse:
    if len(errors) == 1:
        return _response(422, errors[0].error)
    return _response(422, INVALID_DATA, detail=errors)


def _response(
    status_code: int, message: str, detail: list[FieldError] | None = None
) -> JSONResponse:
    body: ApiResponse[None] = ApiResponse(message=message, detail=detail)
    return JSONResponse(status_code=status_code, content=body.model_dump())
