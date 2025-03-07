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
    """
    Manages JWT token operations - generation, verification, and refreshing.
    """

    @staticmethod
    def generate_access_token(user_id: str, username: str) -> str:
        """Generate a short-lived access token."""
        payload = {
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRY_MINUTES),
            "iat": datetime.datetime.utcnow(),
            "sub": user_id,
            "username": username,
            "token_type": "access",
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def generate_refresh_token(user_id: str, username: str) -> str:
        """Generate a long-lived refresh token."""
        payload = {
            "exp": datetime.datetime.utcnow()
            + datetime.timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
            "iat": datetime.datetime.utcnow(),
            "sub": user_id,
            "username": username,
            "token_type": "refresh",
        }
        return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    @staticmethod
    def generate_token_pair(user_id: str, username: str) -> Dict[str, str]:
        """Generate both access and refresh tokens for a user."""
        return {
            "access_token": JWTManager.generate_access_token(user_id, username),
            "refresh_token": JWTManager.generate_refresh_token(user_id, username),
            "token_type": "Bearer",
        }

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
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
        """Create a new access token using a refresh token."""
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
