from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi.responses import JSONResponse

if TYPE_CHECKING:
    from fastapi import Request


class AppError(Exception):
    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, details: list[Any] | None = None, **kwargs: Any) -> None:
        super().__init__(message)
        self.message = message
        self.kwargs = kwargs
        self.details = details or []


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationError(AppError):
    status_code = 400
    code = "VALIDATION_ERROR"


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"


class ForbiddenError(AppError):
    status_code = 403
    code = "FORBIDDEN"


class UnauthorizedError(AppError):
    status_code = 401
    code = "UNAUTHORIZED"


class RateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMITED"


class OptimisticLockError(ConflictError):
    code = "OPTIMISTIC_LOCK_CONFLICT"


def _error_envelope(exc: AppError) -> dict[str, Any]:
    return {
        "error": {
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        }
    }


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    from app.i18n import get_request_language, translate  # local import avoids circular dep

    lang = get_request_language(request.headers.get("Accept-Language", "en"))
    translated = translate(exc.message, lang, **exc.kwargs)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": translated, "details": exc.details}},
    )
