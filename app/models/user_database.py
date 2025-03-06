import re
from typing import Any, Dict, Optional

import bcrypt

from app.config import USERS_FILE
from app.utils import JsonFileManager


class UserDatabase:
    """
    Singleton class for managing user data storage and credential validation.

    Handles user database operations:
    - User data storage and retrieval
    - Password hashing and validation
    - User credential verification
    - Data validation (email format, password strength)
    """

    _instance = None

    def __new__(cls):
        """
        Implement singleton pattern to ensure only one instance exists.

        Returns:
            UserDatabase instance
        """
        if cls._instance is None:
            cls._instance = super(UserDatabase, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, file_path=USERS_FILE):
        """
        Initialize the UserDatabase.

        Args:
            file_path: Path to the JSON file storing user data
        """
        # Ensure initialization happens only once
        if not self._initialized:
            self._file_path = file_path
            JsonFileManager.ensure_file_exists(file_path)
            self._initialized = True

    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format.

        Args:
            email: Email address to validate

        Returns:
            bool: True if email is valid, False otherwise
        """
        if not email:
            return False

        email_regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_regex, email) is not None

    @staticmethod
    def validate_password_strength(password: str) -> bool:
        """
        Check password strength.

        Args:
            password: Password to validate

        Returns:
            bool: True if password meets strength requirements
        """
        # Minimum requirements:
        # - At least 8 characters long
        # - Contains at least one uppercase letter
        # - Contains at least one lowercase letter
        # - Contains at least one number
        # - Contains at least one special character

        if len(password) < 8:
            return False

        has_upper = any(char.isupper() for char in password)
        has_lower = any(char.islower() for char in password)
        has_digit = any(char.isdigit() for char in password)
        has_special = any(not char.isalnum() for char in password)

        return has_upper and has_lower and has_digit and has_special

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            str: Hashed password (includes salt)
        """
        # Convert password to bytes and hash
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def username_exists(self, username: str) -> bool:
        """
        Check if a username already exists in the database.

        Args:
            username: The username to check

        Returns:
            bool: True if username exists, False otherwise
        """
        users = JsonFileManager.read_json(self._file_path)
        return any(user["username"] == username for user in users)

    def email_exists(self, email: str) -> bool:
        """
        Check if an email already exists in the database.

        Args:
            email: The email to check

        Returns:
            bool: True if email exists, False otherwise
        """
        users = JsonFileManager.read_json(self._file_path)
        return any(user["email"] == email for user in users)

    def add_user(self, user_data: Dict[str, Any]) -> None:
        """
        Add a new user to the database with validation.

        Args:
            user_data: Dictionary containing user information

        Returns:
            str: The user's ID

        Raises:
            ValueError: If any validation checks fail
        """
        # Validate required fields
        required_fields = ["username", "email", "password", "id"]
        for field in required_fields:
            if field not in user_data:
                raise ValueError(f"Missing required field: {field}")

        # Validate username uniqueness
        if self.username_exists(user_data["username"]):
            raise ValueError("Username already exists")

        # Validate email uniqueness
        if self.email_exists(user_data["email"]):
            raise ValueError("Email already exists")

        # Validate email format
        if not self.validate_email(user_data["email"]):
            raise ValueError("Invalid email format")

        # Validate password strength if it's not already hashed
        if not user_data.get("password", "").startswith("$2b$"):
            if not self.validate_password_strength(user_data["password"]):
                raise ValueError("Password does not meet strength requirements")
            # Hash the password
            user_data["password"] = self._hash_password(user_data["password"])

        # Add user to database
        users = JsonFileManager.read_json(self._file_path)
        users.append(user_data)
        JsonFileManager.write_json(self._file_path, users)

        return

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by username.

        Args:
            username: The username to search for

        Returns:
            Optional dictionary of user data, or None if not found
        """
        users = JsonFileManager.read_json(self._file_path)
        for user in users:
            if user["username"] == username:
                return user
        return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by email.

        Args:
            email: The email to search for

        Returns:
            Optional dictionary of user data, or None if not found
        """
        users = JsonFileManager.read_json(self._file_path)
        for user in users:
            if user["email"] == email:
                return user
        return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user by user ID.

        Args:
            user_id: The user ID to search for

        Returns:
            Optional dictionary of user data, or None if not found
        """
        users = JsonFileManager.read_json(self._file_path)
        for user in users:
            if user["id"] == user_id:
                return user
        return None

    def update_user(self, username: str, updated_data: Dict[str, Any]) -> bool:
        """
        Update user information in the database with validation.

        Args:
            username: The username of the user to update
            updated_data: Dictionary of fields to update

        Returns:
            bool: True if update was successful, False otherwise

        Raises:
            ValueError: If validation fails
        """
        users = JsonFileManager.read_json(self._file_path)

        # Find the user
        for i, user in enumerate(users):
            if user["username"] == username:
                # Don't allow changing username or id
                if "username" in updated_data:
                    del updated_data["username"]
                if "id" in updated_data:
                    del updated_data["id"]

                # Validate email if being updated
                if "email" in updated_data:
                    # Check email format
                    if not self.validate_email(updated_data["email"]):
                        raise ValueError("Invalid email format")

                    # Check if email already exists
                    if (
                        self.email_exists(updated_data["email"])
                        and updated_data["email"] != user["email"]
                    ):
                        raise ValueError("Email is already in use by another account")

                # Validate and hash password if being updated
                if "password" in updated_data:
                    if not self.validate_password_strength(updated_data["password"]):
                        raise ValueError("Password does not meet strength requirements")
                    updated_data["password"] = self._hash_password(
                        updated_data["password"]
                    )

                # Update the user data
                users[i].update(updated_data)
                JsonFileManager.write_json(self._file_path, users)
                return True

        return False

    def validate_credentials(
        self, username_or_email: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """
        Validate user credentials using bcrypt.

        Args:
            username_or_email: The username or email to validate
            password: The password to check

        Returns:
            Optional user data dictionary if credentials are valid, None otherwise
        """
        # Try to find user by username or email
        user_data = self.get_user(username_or_email) or self.get_user_by_email(
            username_or_email
        )
        if not user_data:
            return None

        # Check password using bcrypt's checkpw method
        if bcrypt.checkpw(
            password.encode("utf-8"), user_data["password"].encode("utf-8")
        ):
            return user_data

        return None
