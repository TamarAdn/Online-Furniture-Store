"""Module docstring."""

import uuid
from typing import Dict, Optional, Tuple

from app.models.jwt_manager import JWTManager
from app.models.user import User
from app.models.user_database import UserDatabase
from app.utils import AuthenticationError


class UserManager:
    """
    Manages user operations and authentication flow.

    This class orchestrates the user management workflow, handling operations like:
    - User registration
    - Authentication and token handling
    - Login/logout processes
    - Profile management
    - Session security
    """

    def __init__(self, user_db: UserDatabase, jwt_manager: JWTManager):
        """
        Initialize UserManager with required dependencies.

        Args:
            user_db: UserDatabase instance
            jwt_manager: JWTManager instance
        """
        self._user_db = user_db
        self._jwt_manager = jwt_manager

    def register_user(
        self,
        username: str,
        full_name: str,
        email: str,
        password: str,
        shipping_address: Optional[str] = None,
    ) -> User:
        """
        Register a new user in the system.

        Args:
            username: User's chosen username
            full_name: User's full name
            email: User's email address
            password: User's password
            shipping_address: Optional shipping address

        Returns:
            User: Newly created user object

        Raises:
            ValueError: If validation fails or user already exists
        """
        # Generate unique user ID
        user_id = str(uuid.uuid4())

        # Prepare user data
        user_data = {
            "id": user_id,
            "username": username,
            "full_name": full_name,
            "email": email,
            "password": password,  # Will be hashed by UserDatabase
            "shipping_address": shipping_address,
        }

        try:
            # Add user to database - all validation happens in the database layer
            self._user_db.add_user(user_data)

            # Create and return User object
            return User(user_id, username, full_name, email, shipping_address)
        except ValueError as e:
            # Raise validation error
            raise ValueError(f"User registration failed: {str(e)}")

    def login(
        self, username_or_email: str, password: str
    ) -> Tuple[User, Dict[str, str]]:
        """
        Authenticate a user and generate JWT tokens.

        Args:
            username_or_email: User's username or email
            password: User's password

        Returns:
            Tuple of (User object, Token dictionary containing
            access_token and refresh_token)

        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Authenticate user - validation happens in database layer
        user_data = self._user_db.validate_credentials(username_or_email, password)

        if not user_data:
            raise AuthenticationError("Invalid username/email or password")

        # Create JWT tokens
        tokens = self._jwt_manager.generate_token_pair(
            user_data["id"], user_data["username"]
        )

        # Create User object
        user = User(
            user_data["id"],
            user_data["username"],
            user_data["full_name"],
            user_data["email"],
            user_data.get("shipping_address"),
        )

        # Set the access token
        user.token = tokens["access_token"]

        return user, tokens

    def authenticate_with_token(self, token: str) -> User:
        """Authenticate a user using JWT access token."""
        try:
            # Verify and decode the token
            payload = self._jwt_manager.verify_token(token)

            # Ensure payload is valid
            if not payload or "token_type" not in payload:
                raise AuthenticationError("Invalid token")

            # Check if it's an access token
            if payload.get("token_type") != "access":
                raise AuthenticationError("Invalid token type for authentication")

            # Get user data from database
            # Get user ID from payload
            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationError("Invalid user identifier in token")

            # Get user data from database
            user_data = self._user_db.get_user_by_id(user_id)

            if not user_data:
                raise AuthenticationError("User not found")

            # Create User object
            user = User(
                user_data["id"],
                user_data["username"],
                user_data["full_name"],
                user_data["email"],
                user_data.get("shipping_address"),
            )

            # Set the token
            user.token = token

            return user
        except Exception as e:
            raise AuthenticationError(str(e))

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Get a new access token using a refresh token.

        Args:
            refresh_token: The refresh token

        Returns:
            str: A new access token

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        try:
            # Use JWTManager to refresh the token
            return self._jwt_manager.refresh_access_token(refresh_token)
        except AuthenticationError as e:
            raise e

    def logout(self, user: User) -> bool:
        """
        Logout a user by clearing their token.

        Args:
            user: User to logout

        Returns:
            bool: True if successful, False otherwise
        """
        if user:
            user.token = None
            return True
        return False

    def update_user(
        self,
        username: str,
        full_name: Optional[str] = None,
        email: Optional[str] = None,
        shipping_address: Optional[str] = None,
    ) -> bool:
        """
        Update user profile information.

        Args:
            username: Username of user to update
            full_name: Optional new full name
            email: Optional new email
            shipping_address: Optional new shipping address

        Returns:
            bool: True if update was successful

        Raises:
            ValueError: If email format is invalid
        """
        updated_data = {}

        if full_name:
            updated_data["full_name"] = full_name

        if email:
            updated_data["email"] = email

        if shipping_address:
            updated_data["shipping_address"] = shipping_address

        # If there's nothing to update, return success
        if not updated_data:
            return True

        # Update user in database - validation happens in database layer
        try:
            return self._user_db.update_user(username, updated_data)
        except ValueError as e:
            # Re-raise the validation error
            raise ValueError(f"User update failed: {str(e)}")

    def update_password(
        self, username: str, current_password: str, new_password: str
    ) -> bool:
        """
        Update a user's password.

        Args:
            username: Username of the user
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            bool: True if password was updated successfully

        Raises:
            AuthenticationError: If current password is incorrect
            ValueError: If new password doesn't meet strength requirements
        """
        # Verify current password
        user_data = self._user_db.validate_credentials(username, current_password)
        if not user_data:
            raise AuthenticationError("Current password is incorrect")

        # Update the password - validation and hashing happen in database layer
        try:
            return self._user_db.update_user(username, {"password": new_password})
        except ValueError as e:
            # Re-raise the validation error
            raise ValueError(f"Password update failed: {str(e)}")
