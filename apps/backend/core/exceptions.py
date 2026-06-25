class AppException(Exception):
    status_code: int = 500
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None) -> None:
        self.detail = detail if detail is not None else self.detail
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code: int = 404
    detail: str = "Resource not found."


class UnauthorizedError(AppException):
    status_code: int = 401
    detail: str = "Authentication required."


class ForbiddenError(AppException):
    status_code: int = 403
    detail: str = "You do not have permission to perform this action."


class ConflictError(AppException):
    status_code: int = 409
    detail: str = "Resource conflict."


class ValidationError(AppException):
    status_code: int = 422
    detail: str = "Validation failed."


class ExternalServiceError(AppException):
    status_code: int = 502
    detail: str = "An upstream service request failed."
