from fastapi import FastAPI

from app.owner_profile.infrastructure.api.exception_handlers import (
    register_exception_handlers,
)
from app.owner_profile.infrastructure.api.lambda_handler import lambda_handler
from app.owner_profile.infrastructure.api.v1_router import router as v1_router
from config.settings import settings

app = FastAPI(title='TurfBook Owner Service')

app.include_router(v1_router, prefix=settings.api_prefix)
register_exception_handlers(app)

handler = lambda_handler(app)
