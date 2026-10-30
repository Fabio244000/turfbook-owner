from pydantic import BaseModel


class FieldError(BaseModel):
    field: str
    error: str


class ApiResponse[T](BaseModel):
    success: bool = False
    message: str = ''
    detail: list[FieldError] | None = None
    data: T | None = None
