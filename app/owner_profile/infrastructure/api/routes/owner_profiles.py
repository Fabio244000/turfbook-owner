from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.owner_profile.domain.ports.input.register_owner_profile_port import (
    RegisterOwnerProfilePort,
)
from app.owner_profile.infrastructure.api.dependencies import (
    get_current_user_uuid,
    get_register_owner_profile_use_case,
)
from app.owner_profile.infrastructure.api.schemas.api_response import ApiResponse
from app.owner_profile.infrastructure.api.schemas.owner_profile_schema import (
    OwnerProfileRequest,
    RegisterOwnerProfileData,
)

router = APIRouter()


@router.post(
    '/owner-profiles',
    status_code=status.HTTP_201_CREATED,
    response_model=ApiResponse[RegisterOwnerProfileData],
)
async def register_owner_profile(
    request: OwnerProfileRequest,
    user_uuid: UUID = Depends(get_current_user_uuid),
    use_case: RegisterOwnerProfilePort = Depends(get_register_owner_profile_use_case),
) -> ApiResponse[RegisterOwnerProfileData]:
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
