from pydantic import BaseModel
from typing import Any, Optional


class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[Any] = None


class AppError(Exception):
    def __init__(self, error: str, message: str, status_code: int = 400, detail: Any = None):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(message)


class HealthResponse(BaseModel):
    status: str
    cache_initialized: bool
    year: int
