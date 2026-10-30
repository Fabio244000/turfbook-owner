from fastapi import APIRouter

from app.owner_profile.infrastructure.api.routes.owner_profiles import (
    router as owner_profiles_router,
)

API_VERSION_PREFIX = '/v1'

router = APIRouter(prefix=API_VERSION_PREFIX)
router.include_router(owner_profiles_router)
