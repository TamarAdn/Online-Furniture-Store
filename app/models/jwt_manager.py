"""JWT Manager module for token handling operations."""

import datetime
from typing import Any, Dict

import jwt

from app.config import (
    ACCESS_TOKEN_EXPIRY_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRY_DAYS,
)
from app.utils import AuthenticationError


class JWTManager:
    """Manages JWT token operations - generation, verification, and refreshing."""

    @staticmethod
    def _generate_token(
        user_id: str, username: str, expiry_delta: datetime.timedelta, token_type: str
    ) -> str:
        """
        Generate a token with a given expiry and type.

        Args:
            user_id: Unique identifier for the user
            username: Username for the user
            expiry_delta: Time until token expiry
            token_type: Type of token ("access" or "refresh")

        Returns:
            str: Encoded JWT token
        """
        payload = {
            "exp": datetime.datetime.utcnow() + expiry_delta,
            "iat": datetime.datetime.utcnow(),
            "sub": user_id,
            "username": username,
            "token_type": token_type,
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def generate_access_token(user_id: str, username: str) -> str:
        """
        Generate a short-lived access token.

        Args:
            user_id: Unique identifier for the user
            username: Username for the user

        Returns:
            str: Encoded JWT access token
        """
        return JWTManager._generate_token(
            user_id,
            username,
            datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES),
            "access",
        )

    @staticmethod
    def generate_refresh_token(user_id: str, username: str) -> str:
        """
        Generate a long-lived refresh token.

        Args:
            user_id: Unique identifier for the user
            username: Username for the user

        Returns:
            str: Encoded JWT refresh token
        """
        return JWTManager._generate_token(
            user_id,
            username,
            datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
            "refresh",
        )

    @staticmethod
    def generate_token_pair(user_id: str, username: str) -> Dict[str, str]:
        """
        Generate both access and refresh tokens for a user.

        Args:
            user_id: Unique identifier for the user
            username: Username for the user

        Returns:
            Dict[str, str]: Dictionary containing access_token,
            refresh_token and token_type
        """
        return {
            "access_token": JWTManager.generate_access_token(user_id, username),
            "refresh_token": JWTManager.generate_refresh_token(user_id, username),
            "token_type": "Bearer",
        }

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """
        Verify and decode a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Dict[str, Any]: Decoded token payload

        Raises:
            AuthenticationError: If token verification fails
        """
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Authentication token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid authentication token")
        except Exception as e:
            raise AuthenticationError(f"Token verification failed: {str(e)}")

    @staticmethod
    def refresh_access_token(refresh_token: str) -> str:
        """
        Create a new access token using a refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            str: New access token

        Raises:
            AuthenticationError: If token refresh fails
        """
        try:
            # Verify the refresh token
            payload = JWTManager.verify_token(refresh_token)

            # Check if it's a refresh token
            if payload.get("token_type") != "refresh":
                raise AuthenticationError("Invalid token type for refresh")

            # Extract user information
            user_id = payload["sub"]
            username = payload.get("username")

            # Generate new access token
            return JWTManager.generate_access_token(user_id, username)
        except AuthenticationError:
            raise
        except Exception as e:
            raise AuthenticationError(f"Failed to refresh token: {str(e)}")
