import pytest
from core.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)


@pytest.mark.parametrize(
    "exc_class,expected_status_code",
    [
        (NotFoundError, 404),
        (UnauthorizedError, 401),
        (ForbiddenError, 403),
        (ConflictError, 409),
        (ValidationError, 422),
    ],
)
def test_default_status_code(exc_class: type[AppException], expected_status_code: int) -> None:
    exc = exc_class()
    assert exc.status_code == expected_status_code


@pytest.mark.parametrize(
    "exc_class",
    [NotFoundError, UnauthorizedError, ForbiddenError, ConflictError, ValidationError],
)
def test_detail_can_be_overridden(exc_class: type[AppException]) -> None:
    exc = exc_class(detail="custom detail message")
    assert exc.detail == "custom detail message"


@pytest.mark.parametrize(
    "exc_class",
    [NotFoundError, UnauthorizedError, ForbiddenError, ConflictError, ValidationError],
)
def test_is_instance_of_app_exception(exc_class: type[AppException]) -> None:
    exc = exc_class()
    assert isinstance(exc, AppException)
