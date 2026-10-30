from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from mangum import Mangum

from app.owner_profile.domain.exceptions import DomainError
from app.owner_profile.infrastructure.api.exception_handlers import (
    domain_error_handler,
    request_validation_handler,
    unexpected_error_handler,
)
from app.owner_profile.infrastructure.api.v1_router import router as v1_router
from config.settings import settings

app = FastAPI(title='TurfBook Owner Service')

app.include_router(v1_router, prefix=settings.api_prefix)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_exception_handler(RequestValidationError, request_validation_handler)
app.add_exception_handler(Exception, unexpected_error_handler)

handler = Mangum(app, lifespan='off')
