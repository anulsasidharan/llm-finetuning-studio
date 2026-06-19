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
    # Tamper a character a few positions before the end, not the very last
    # one: base64url's final character of a non-multiple-of-3-byte payload
    # (HS256 signatures are 32 bytes) carries unused padding bits that some
    # decoders ignore, so flipping only the last char has a real chance of
    # producing a string that decodes to the identical signature bytes —
    # i.e. it doesn't actually tamper anything, and decode_token correctly
    # doesn't raise. A middle character has no such ambiguity.
    pos = -5
    original_char = token[pos]
    replacement = "a" if original_char != "a" else "b"
    tampered = token[: len(token) + pos] + replacement + token[len(token) + pos + 1 :]
    with pytest.raises(HTTPException) as exc_info:
        decode_token(tampered)
    assert exc_info.value.status_code == 401


def test_decode_token_raises_on_invalid_signature() -> None:
    token = jwt.encode({"sub": "user-123"}, "wrong-secret-key", algorithm=settings.ALGORITHM)
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401
