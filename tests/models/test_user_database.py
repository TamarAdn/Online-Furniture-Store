from typing import Any, Dict, List

import bcrypt
import pytest

from app.models.user_database import UserDatabase
from app.utils import JsonFileManager


# Fixture to reset the singleton and patch JsonFileManager methods
@pytest.fixture(autouse=True)
def reset_user_database():
    """Reset the UserDatabase singleton and mock the JsonFileManager methods."""
    UserDatabase._instance = None
    # Use an in-memory list to simulate the JSON file storage.
    storage: List[Dict[str, Any]] = []

    def dummy_ensure(file_path):
        pass

    def dummy_read(file_path):
        return storage

    def dummy_write(file_path, data):
        nonlocal storage
        storage = data

    JsonFileManager.ensure_file_exists = dummy_ensure
    JsonFileManager.read_json = dummy_read
    JsonFileManager.write_json = dummy_write
    yield storage  # tests can inspect storage if needed


# ---------------------------
# Tests for static validation methods
# ---------------------------
@pytest.mark.parametrize(
    "email,expected",
    [
        ("user@example.com", True),
        ("user.name+tag@domain.co", True),
        ("user@sub.domain.com", True),
        ("invalid-email", False),
        ("user@.com", False),
        ("", False),
        (None, False),  # None will fail the "if not email" check
    ],
)
def test_validate_email(email, expected) -> None:
    """Test the email validation function with various
    valid and invalid email formats."""
    # Since the method expects a string, protect against None:
    result = UserDatabase.validate_email("" if email is None else email)
    assert result is expected


@pytest.mark.parametrize(
    "password,expected",
    [
        ("Aa1!aaaa", True),  # meets all requirements
        ("Aa1!aa", False),  # too short
        ("aaaaaaaa", False),  # no uppercase, digit, special
        ("AAAAAAAA", False),  # no lowercase, digit, special
        ("AaAAAAAA", False),  # no digit, special
        ("Aa1AAAAA", False),  # no special character
    ],
)
def test_validate_password_strength(password, expected) -> None:
    """Test password strength validation against various password patterns."""
    result = UserDatabase.validate_password_strength(password)
    assert result is expected


# ---------------------------
# Tests for username_exists and email_exists
# ---------------------------
def test_username_exists(reset_user_database) -> None:
    """Test that username existence check correctly identifies
    existing and non-existing usernames."""
    reset_user_database.extend(
        [
            {
                "username": "user1",
                "email": "u1@example.com",
                "password": "hashed",
                "id": "U1",
            },
            {
                "username": "user2",
                "email": "u2@example.com",
                "password": "hashed",
                "id": "U2",
            },
        ]
    )
    db = UserDatabase()
    assert db.username_exists("user1") is True
    assert db.username_exists("nonexistent") is False


def test_email_exists(reset_user_database) -> None:
    """Test that email existence check correctly identifies
    existing and non-existing email addresses."""
    reset_user_database.extend(
        [
            {
                "username": "user1",
                "email": "u1@example.com",
                "password": "hashed",
                "id": "U1",
            },
        ]
    )
    db = UserDatabase()
    assert db.email_exists("u1@example.com") is True
    assert db.email_exists("u2@example.com") is False


# ---------------------------
# Tests for add_user
# ---------------------------
@pytest.mark.parametrize(
    "user_data, error_msg",
    [
        (
            {"email": "test@example.com", "password": "Aa1!aaaa", "id": "U1"},
            "Missing required field: username",
        ),
        (
            {"username": "user", "password": "Aa1!aaaa", "id": "U1"},
            "Missing required field: email",
        ),
        (
            {"username": "user", "email": "test@example.com", "id": "U1"},
            "Missing required field: password",
        ),
        (
            {"username": "user", "email": "test@example.com", "password": "Aa1!aaaa"},
            "Missing required field: id",
        ),
    ],
)
def test_add_user_missing_fields(user_data, error_msg, reset_user_database) -> None:
    """Test that adding users with missing required fields raises appropriate
    ValueError exceptions."""
    db = UserDatabase()
    with pytest.raises(ValueError, match=error_msg):
        db.add_user(user_data)


def test_add_user_duplicate_username(reset_user_database) -> None:
    """Test that attempting to add a user with an existing
    username raises appropriate error."""
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "u1@example.com",
                "password": "hashed",
                "id": "U1",
            }
        ]
    )
    db = UserDatabase()
    user_data = {
        "username": "user",
        "email": "new@example.com",
        "password": "Aa1!aaaa",
        "id": "U2",
    }
    with pytest.raises(ValueError, match="Username already exists"):
        db.add_user(user_data)


def test_add_user_duplicate_email(reset_user_database) -> None:
    """Test that attempting to add a user with an existing email
    raises appropriate error."""
    reset_user_database.extend(
        [
            {
                "username": "user1",
                "email": "u1@example.com",
                "password": "hashed",
                "id": "U1",
            }
        ]
    )
    db = UserDatabase()
    user_data = {
        "username": "user2",
        "email": "u1@example.com",
        "password": "Aa1!aaaa",
        "id": "U2",
    }
    with pytest.raises(ValueError, match="Email already exists"):
        db.add_user(user_data)


@pytest.mark.parametrize("email", ["invalid-email", "user@.com", ""])
def test_add_user_invalid_email_format(email, reset_user_database) -> None:
    """Test that adding a user with invalid email format raises appropriate error."""
    db = UserDatabase()
    user_data = {"username": "user", "email": email, "password": "Aa1!aaaa", "id": "U1"}
    with pytest.raises(ValueError, match="Invalid email format"):
        db.add_user(user_data)


# Parameterized tests for various weak passwords.
@pytest.mark.parametrize(
    "weak_password",
    [
        "short1!",  # 7 characters, too short.
        "alllowercase1!",  # no uppercase.
        "ALLUPPERCASE1!",  # no lowercase.
        "NoDigits!",  # no digit.
        "NoSpecial1",  # no special character.
    ],
)
def test_add_user_weak_passwords(reset_user_database, weak_password) -> None:
    """Test that adding a user with weak passwords raises appropriate error."""
    db = UserDatabase()
    user_data = {
        "username": "user",
        "email": "test@example.com",
        "password": weak_password,
        "id": "U1",
    }
    with pytest.raises(
        ValueError, match="Password does not meet strength requirements"
    ):
        db.add_user(user_data)


# Dedicated test for a 7-character password ("aaaaaaa") to ensure the branch is hit.
def test_add_user_weak_password_short(reset_user_database) -> None:
    """Test that adding a user with a too-short password raises appropriate error."""
    db = UserDatabase()
    user_data = {
        "username": "user",
        "email": "test@example.com",
        "password": "aaaaaaa",  # 7 characters, too short.
        "id": "U1",
    }
    with pytest.raises(
        ValueError, match="Password does not meet strength requirements"
    ):
        db.add_user(user_data)


def test_add_user_success(reset_user_database) -> None:
    """Test successful user addition with valid data."""
    db = UserDatabase()
    user_data = {
        "username": "user",
        "email": "test@example.com",
        "password": "Aa1!aaaa",
        "id": "U1",
    }
    db.add_user(user_data)
    stored_user = reset_user_database[0]
    assert stored_user["username"] == "user"
    assert stored_user["email"] == "test@example.com"
    assert stored_user["password"].startswith("$2b$")


# ---------------------------
# Tests for get_user, get_user_by_email, get_user_by_id
# ---------------------------
def test_get_user(reset_user_database) -> None:
    """Test retrieving a user by username works correctly."""
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "test@example.com",
                "password": "hashed",
                "id": "U1",
            }
        ]
    )
    db = UserDatabase()
    user = db.get_user("user")
    assert user is not None
    assert user["id"] == "U1"
    assert db.get_user("nonexistent") is None


def test_get_user_by_email(reset_user_database) -> None:
    """Test retrieving a user by email works correctly."""
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "test@example.com",
                "password": "hashed",
                "id": "U1",
            }
        ]
    )
    db = UserDatabase()
    user = db.get_user_by_email("test@example.com")
    assert user is not None
    assert user["username"] == "user"
    assert db.get_user_by_email("no@example.com") is None


def test_get_user_by_id(reset_user_database) -> None:
    """Test retrieving a user by ID works correctly."""
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "test@example.com",
                "password": "hashed",
                "id": "U1",
            }
        ]
    )
    db = UserDatabase()
    user = db.get_user_by_id("U1")
    assert user is not None
    assert user["username"] == "user"
    assert db.get_user_by_id("U2") is None


# ---------------------------
# Tests for update_user
# ---------------------------
def test_update_user_not_found(reset_user_database) -> None:
    """Test that attempting to update a non-existent user returns False."""
    db = UserDatabase()
    result = db.update_user("nonexistent", {"email": "new@example.com"})
    assert result is False


def test_update_user_invalid_email_format(reset_user_database) -> None:
    """Test that updating a user with invalid email format raises appropriate error."""
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "old@example.com",
                "password": "hashed",
                "id": "U1",
            }
        ]
    )
    db = UserDatabase()
    with pytest.raises(ValueError, match="Invalid email format"):
        db.update_user("user", {"email": "bad-email"})


def test_update_user_email_duplicate(reset_user_database) -> None:
    """Test that updating a user with an email already in use
    by another account raises appropriate error."""
    reset_user_database.extend(
        [
            {
                "username": "user1",
                "email": "a@example.com",
                "password": "hashed",
                "id": "U1",
            },
            {
                "username": "user2",
                "email": "b@example.com",
                "password": "hashed",
                "id": "U2",
            },
        ]
    )
    db = UserDatabase()
    with pytest.raises(ValueError, match="Email is already in use by another account"):
        db.update_user("user2", {"email": "a@example.com"})


def test_update_user_password(reset_user_database) -> None:
    """Test that updating a user's password works correctly."""
    db = UserDatabase()
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "test@example.com",
                "password": "$2b$hashed",
                "id": "U1",
            }
        ]
    )
    result = db.update_user("user", {"password": "Aa1!bbbb"})
    assert result is True
    updated_user = reset_user_database[0]
    assert updated_user["password"].startswith("$2b$")
    assert updated_user["password"] != "Aa1!bbbb"


# Parameterized tests for weak updated passwords.
@pytest.mark.parametrize(
    "weak_password",
    [
        "short",  # too short.
        "alllowercase",  # no uppercase/digit/special.
        "ALLUPPERCASE1",  # no lowercase/special.
        "NoSpecial1",  # no special character.
    ],
)
def test_update_user_weak_password(reset_user_database, weak_password) -> None:
    """Test that updating a user with weak passwords raises appropriate error."""
    db = UserDatabase()
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "test@example.com",
                "password": "$2b$hashed",
                "id": "U1",
            }
        ]
    )
    with pytest.raises(
        ValueError, match="Password does not meet strength requirements"
    ):
        db.update_user("user", {"password": weak_password})


def test_update_user_ignore_username_and_id(reset_user_database) -> None:
    """Test that user updates ignore attempts to change username and ID."""
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "test@example.com",
                "password": "$2b$hashed",
                "id": "U1",
            }
        ]
    )
    db = UserDatabase()
    result = db.update_user(
        "user", {"username": "newuser", "id": "U999", "email": "new@example.com"}
    )
    assert result is True
    updated_user = reset_user_database[0]
    assert updated_user["username"] == "user"
    assert updated_user["id"] == "U1"
    assert updated_user["email"] == "new@example.com"


# ---------------------------
# Tests for validate_credentials
# ---------------------------
def test_validate_credentials_user_not_found(reset_user_database) -> None:
    """Test that validating credentials for a non-existent user returns None."""
    db = UserDatabase()
    result = db.validate_credentials("nonexistent", "any")
    assert result is None


def test_validate_credentials_wrong_password(reset_user_database) -> None:
    """Test that validating credentials with incorrect password returns None."""
    plain = "Aa1!cccc"
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    reset_user_database.extend(
        [
            {
                "username": "user",
                "email": "test@example.com",
                "password": hashed,
                "id": "U1",
            }
        ]
    )
    db = UserDatabase()
    result = db.validate_credentials("user", "wrongpass")
    assert result is None


def test_validate_credentials_success_by_username(reset_user_database) -> None:
    """Test successful credential validation using username."""
    plain = "Aa1!cccc"
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_data = {
        "username": "user",
        "email": "test@example.com",
        "password": hashed,
        "id": "U1",
    }
    reset_user_database.append(user_data)
    db = UserDatabase()
    result = db.validate_credentials("user", plain)
    assert result is not None
    assert result["username"] == "user"


def test_validate_credentials_success_by_email(reset_user_database) -> None:
    """Test successful credential validation using email."""
    plain = "Aa1!cccc"
    hashed = bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_data = {
        "username": "user",
        "email": "test@example.com",
        "password": hashed,
        "id": "U1",
    }
    reset_user_database.append(user_data)
    db = UserDatabase()
    result = db.validate_credentials("test@example.com", plain)
    assert result is not None
    assert result["email"] == "test@example.com"
