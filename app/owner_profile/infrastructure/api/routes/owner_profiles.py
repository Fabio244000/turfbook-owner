from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Depends, status

from app.owner_profile.application.ports.driving.get_owner_profile_port import (
    GetOwnerProfilePort,
)
from app.owner_profile.domain.ports.input.register_owner_profile_port import (
    RegisterOwnerProfilePort,
)
from app.owner_profile.infrastructure.api.api_docs.owner_profiles import (
    GET_OWNER_PROFILE_DOCS,
    REGISTER_OWNER_PROFILE_DOCS,
    REGISTER_OWNER_PROFILE_REQUEST_EXAMPLES,
)
from app.owner_profile.infrastructure.api.dependencies import (
    get_current_user_uuid,
    get_get_owner_profile_use_case,
    get_register_owner_profile_use_case,
)
from app.owner_profile.infrastructure.api.schemas.api_response import ApiResponse
from app.owner_profile.infrastructure.api.schemas.owner_profile_schema import (
    GetOwnerProfileData,
    OwnerProfileRequest,
    RegisterOwnerProfileData,
)

router = APIRouter()


@router.post(
    '/owner-profiles',
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[RegisterOwnerProfileData],
    **REGISTER_OWNER_PROFILE_DOCS,
)
async def register_owner_profile(
    request: Annotated[
        OwnerProfileRequest,
        Body(openapi_examples=REGISTER_OWNER_PROFILE_REQUEST_EXAMPLES),
    ],
    user_uuid: UUID = Depends(get_current_user_uuid),
    use_case: RegisterOwnerProfilePort = Depends(get_register_owner_profile_use_case),
) -> ApiResponse[RegisterOwnerProfileData]:
    """Registers the owner profile of the session's user, with its RUC, its identity
    document (the default one) and, optionally, its address. A user has at most one
    profile."""
    profile = await use_case.execute(
        user_uuid=user_uuid,
        ruc=request.ruc,
        document_type=request.identity_document.document_type,
        document_number=request.identity_document.document_number,
        address=request.address,
    )
    return ApiResponse(
        success=True, data=RegisterOwnerProfileData.model_validate(profile)
    )


@router.get(
    '/owner-profiles/me',
    status_code=status.HTTP_200_OK,
    response_model=ApiResponse[GetOwnerProfileData],
    **GET_OWNER_PROFILE_DOCS,
)
async def get_owner_profile(
    user_uuid: UUID = Depends(get_current_user_uuid),
    use_case: GetOwnerProfilePort = Depends(get_get_owner_profile_use_case),
) -> ApiResponse[GetOwnerProfileData]:
    """The owner profile of the session's user. A 404 means the user has none: they
    are a player, not an owner."""
    details = await use_case.execute(user_uuid=user_uuid)
    return ApiResponse(success=True, data=GetOwnerProfileData.model_validate(details))
