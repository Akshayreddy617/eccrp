"""ECCRP Unit Tests - Security Utilities."""
import pytest
from datetime import datetime, timezone, timedelta
from jose import jwt

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_access_token,
)
from app.core.config import settings


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        hashed = hash_password("TestPassword@123")
        assert isinstance(hashed, str)
        assert len(hashed) > 20

    def test_verify_correct_password(self):
        hashed = hash_password("TestPassword@123")
        assert verify_password("TestPassword@123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("TestPassword@123")
        assert verify_password("WrongPassword@456", hashed) is False

    def test_different_passwords_produce_different_hashes(self):
        h1 = hash_password("Password@1")
        h2 = hash_password("Password@2")
        assert h1 != h2

    def test_same_password_produces_different_hashes(self):
        """bcrypt uses random salt each time."""
        h1 = hash_password("Password@1")
        h2 = hash_password("Password@1")
        assert h1 != h2

    def test_empty_string_can_be_hashed(self):
        hashed = hash_password("")
        assert verify_password("", hashed) is True


class TestJWTTokens:
    def test_create_access_token_returns_string(self):
        token = create_access_token("user-uuid-123", "candidate")
        assert isinstance(token, str)
        assert len(token) > 50

    def test_decode_valid_token(self):
        token = create_access_token("user-uuid-123", "candidate")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-uuid-123"
        assert payload["role"] == "candidate"
        assert payload["type"] == "access"

    def test_decode_token_with_extra_fields(self):
        token = create_access_token("user-uuid-456", "admin", extra={"org_id": "org-123"})
        payload = decode_access_token(token)
        assert payload["org_id"] == "org-123"

    def test_expired_token_raises(self):
        from fastapi import HTTPException
        # Manually create expired token
        payload = {
            "sub": "user-id",
            "role": "candidate",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            "type": "access",
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(HTTPException) as exc_info:
            decode_access_token(token)
        assert exc_info.value.status_code == 401

    def test_tampered_token_raises(self):
        from fastapi import HTTPException
        token = create_access_token("user-id", "candidate")
        tampered = token[:-5] + "XXXXX"
        with pytest.raises(HTTPException):
            decode_access_token(tampered)

    def test_wrong_secret_raises(self):
        from fastapi import HTTPException
        payload = {
            "sub": "user-id",
            "role": "candidate",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
        with pytest.raises(HTTPException):
            decode_access_token(token)

    def test_non_access_token_type_raises(self):
        from fastapi import HTTPException
        payload = {
            "sub": "user-id",
            "role": "candidate",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "type": "refresh",  # Wrong type
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        with pytest.raises(HTTPException):
            decode_access_token(token)


class TestRefreshToken:
    def test_create_refresh_token_returns_tuple(self):
        raw, hashed = create_refresh_token()
        assert isinstance(raw, str)
        assert isinstance(hashed, str)

    def test_raw_and_hashed_differ(self):
        raw, hashed = create_refresh_token()
        assert raw != hashed

    def test_hashed_is_sha256(self):
        import hashlib
        raw, hashed = create_refresh_token()
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert hashed == expected

    def test_different_calls_produce_different_tokens(self):
        raw1, _ = create_refresh_token()
        raw2, _ = create_refresh_token()
        assert raw1 != raw2

    def test_raw_token_is_url_safe(self):
        import re
        raw, _ = create_refresh_token()
        # URL-safe base64 characters only
        assert re.match(r'^[A-Za-z0-9_\-]+$', raw)
