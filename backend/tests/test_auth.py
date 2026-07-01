"""
Unit tests for JWT authentication module.
Tests token creation, decoding, password hashing, and error cases.
"""

import pytest
from datetime import timedelta
from jose import jwt
from auth.jwt_auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    SECRET_KEY,
    ALGORITHM,
)
from fastapi import HTTPException


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mysecret123")
        assert hashed != "mysecret123"

    def test_verify_correct_password(self):
        hashed = hash_password("mysecret123")
        assert verify_password("mysecret123", hashed) is True

    def test_reject_wrong_password(self):
        hashed = hash_password("mysecret123")
        assert verify_password("wrongpassword", hashed) is False

    def test_same_password_different_hashes(self):
        h1 = hash_password("mypassword")
        h2 = hash_password("mypassword")
        assert h1 != h2


class TestJWTTokens:
    def test_create_and_decode_token(self):
        token = create_access_token({"sub": "user-123", "email": "test@example.com"})
        data = decode_token(token)
        assert data.user_id == "user-123"
        assert data.email == "test@example.com"

    def test_token_has_expiry(self):
        token = create_access_token({"sub": "user-456", "email": "a@b.com"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload

    def test_custom_expiry(self):
        token = create_access_token(
            {"sub": "user-789", "email": "c@d.com"},
            expires_delta=timedelta(hours=1),
        )
        data = decode_token(token)
        assert data.user_id == "user-789"

    def test_invalid_token_raises_401(self):
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises_401(self):
        token = create_access_token({"sub": "user-111", "email": "x@y.com"})
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException) as exc_info:
            decode_token(tampered)
        assert exc_info.value.status_code == 401

    def test_token_missing_sub_raises_401(self):
        token = create_access_token({"email": "no-sub@example.com"})
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        assert exc_info.value.status_code == 401
