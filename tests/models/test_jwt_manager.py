"""Tests for the JWT Manager module."""

import datetime

import jwt
import pytest

from app.config import JWT_ALGORITHM, JWT_SECRET_KEY
from app.models.jwt_manager import JWTManager
from app.utils import AuthenticationError


def decode_token_without_verification(token: str) -> dict:
    """
    Helper function to decode a token without verifying expiry (for testing).

    Args:
        token: JWT token to decode

    Returns:
        dict: Decoded token payload
    """
    return jwt.decode(
        token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM], options={"verify_exp": False}
    )


class TestJWTManager:
    """Test suite for the JWTManager class."""

    def test_generate_access_token(self) -> None:
        """Test access token generation."""
        user_id = "user123"
        username = "testuser"
        token = JWTManager.generate_access_token(user_id, username)
        payload = decode_token_without_verification(token)
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["token_type"] == "access"
        assert "exp" in payload
        assert "iat" in payload

    def test_generate_refresh_token(self) -> None:
        """Test refresh token generation."""
        user_id = "user123"
        username = "testuser"
        token = JWTManager.generate_refresh_token(user_id, username)
        payload = decode_token_without_verification(token)
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["token_type"] == "refresh"
        assert "exp" in payload
        assert "iat" in payload

    def test_generate_token_pair(self) -> None:
        """Test token pair generation."""
        user_id = "user123"
        username = "testuser"
        tokens = JWTManager.generate_token_pair(user_id, username)
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens.get("token_type") == "Bearer"
        access_payload = decode_token_without_verification(tokens["access_token"])
        assert access_payload["token_type"] == "access"
        refresh_payload = decode_token_without_verification(tokens["refresh_token"])
        assert refresh_payload["token_type"] == "refresh"

    def test_verify_token_valid(self) -> None:
        """Test verification of a valid token."""
        user_id = "user123"
        username = "testuser"
        token = JWTManager.generate_access_token(user_id, username)
        payload = JWTManager.verify_token(token)
        assert payload["sub"] == user_id
        assert payload["username"] == username
        assert payload["token_type"] == "access"

    @pytest.mark.parametrize(
        "scenario, token_generator, expected_msg",
        [
            (
                "expired",
                lambda: jwt.encode(
                    {
                        "exp": datetime.datetime.utcnow()
                        - datetime.timedelta(minutes=5),
                        "iat": datetime.datetime.utcnow()
                        - datetime.timedelta(minutes=6),
                        "sub": "user123",
                        "username": "testuser",
                        "token_type": "access",
                    },
                    JWT_SECRET_KEY,
                    algorithm=JWT_ALGORITHM,
                ),
                "expired",
            ),
            ("invalid", lambda: "invalidtoken", "Invalid authentication token"),
            ("generic", None, "Token verification failed: custom error"),
        ],
    )
    def test_verify_token_exceptions(
        self, monkeypatch, scenario: str, token_generator, expected_msg: str
    ) -> None:
        """Test token verification exceptions."""
        if scenario == "generic":

            def fake_decode(*args, **kwargs):
                raise Exception("custom error")

            monkeypatch.setattr(jwt, "decode", fake_decode)
            token = "anytoken"
        else:
            token = token_generator()
        with pytest.raises(AuthenticationError, match=expected_msg):
            JWTManager.verify_token(token)

    def test_refresh_access_token_valid(self) -> None:
        """Test refreshing with a valid refresh token."""
        user_id = "user123"
        username = "testuser"
        refresh_token = JWTManager.generate_refresh_token(user_id, username)
        new_access = JWTManager.refresh_access_token(refresh_token)
        access_payload = decode_token_without_verification(new_access)
        assert access_payload["token_type"] == "access"
        assert access_payload["sub"] == user_id
        assert access_payload["username"] == username

    @pytest.mark.parametrize(
        "scenario, token_generator, expected_msg",
        [
            (
                "wrong_token_type",
                lambda: JWTManager.generate_access_token("user123", "testuser"),
                "Invalid token type for refresh",
            ),
            ("invalid", lambda: "notavalidtoken", "Invalid authentication token"),
            ("generic", None, "Failed to refresh token: refresh error"),
        ],
    )
    def test_refresh_access_token_exceptions(
        self, monkeypatch, scenario: str, token_generator, expected_msg: str
    ) -> None:
        """Test refresh token exceptions."""
        if scenario == "generic":

            def fake_verify(token):
                raise Exception("refresh error")

            monkeypatch.setattr(JWTManager, "verify_token", fake_verify)
            token = "anytoken"
        else:
            token = token_generator()
        with pytest.raises(AuthenticationError, match=expected_msg):
            JWTManager.refresh_access_token(token)
