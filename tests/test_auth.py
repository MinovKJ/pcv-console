"""
Unit tests for auth utilities: password hashing, JWT creation & decoding.
"""
import pytest
from datetime import timedelta
from jose import JWTError
from app.auth.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


def test_password_hashing():
    raw = "SuperSecretPassword123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_access_token_creation_and_decoding():
    user_id = 42
    role = "analyst"
    token = create_access_token(user_id=user_id, role=role)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == role
    assert payload["type"] == "access"
    assert "exp" in payload


def test_refresh_token_creation_and_decoding():
    user_id = 101
    token = create_refresh_token(user_id=user_id)
    payload = decode_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_invalid_token_raises():
    with pytest.raises(JWTError):
        decode_token("invalid.token.payload")

