from datetime import timedelta

import pytest
from core.auth import create_access_token, create_refresh_token, decode_token
from core.config import settings
from fastapi import HTTPException
from jose import jwt


def test_create_access_token_round_trips() -> None:
    token = create_access_token({"sub": "user-123"})
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_create_refresh_token_round_trips() -> None:
    token = create_refresh_token({"sub": "user-456"})
    payload = decode_token(token)
    assert payload["sub"] == "user-456"


def test_decode_token_raises_on_expired_token() -> None:
    token = create_access_token({"sub": "user-123"}, expires_delta=timedelta(seconds=-1))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_decode_token_raises_on_tampered_token() -> None:
    token = create_access_token({"sub": "user-123"})
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")
    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered)
    assert exc_info.value.status_code == 401


def test_decode_token_raises_on_invalid_signature() -> None:
    token = jwt.encode({"sub": "user-123"}, "wrong-secret-key", algorithm=settings.ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401
