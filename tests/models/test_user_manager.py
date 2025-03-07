import pytest

from app.models.user_manager import UserManager
from app.utils import AuthenticationError


# Fake implementation of UserDatabase to simulate behavior
class FakeUserDatabase:
    """Simulates UserDatabase behavior for testing."""

    def __init__(self):
        """Initialize with empty users dictionary."""
        self.users = {}

    def add_user(self, user_data):
        """Add a user to the database."""
        if user_data["username"] in self.users:
            raise ValueError("User already exists")
        self.users[user_data["username"]] = user_data

    def validate_credentials(self, username_or_email, password):
        """Validate user credentials."""
        for user in self.users.values():
            if (
                user["username"] == username_or_email
                or user["email"] == username_or_email
            ) and user["password"] == password:
                return user
        return None

    def get_user_by_id(self, user_id):
        """Get a user by ID."""
        for user in self.users.values():
            if user["id"] == user_id:
                return user
        return None

    def update_user(self, username, updated_data):
        """Update a user's data."""
        if username not in self.users:
            raise ValueError("User not found")
        self.users[username].update(updated_data)
        return True


# Fake implementation of JWTManager to simulate JWT operations
class FakeJWTManager:
    """Simulates JWTManager behavior for testing."""

    def generate_token_pair(self, user_id, username):
        """Generate a fake token pair."""
        return {
            "access_token": f"access_{user_id}",
            "refresh_token": f"refresh_{user_id}",
        }

    def verify_token(self, token):
        """Verify a token and return payload."""
        if token.startswith("access_"):
            user_id = token.split("_", 1)[1]
            return {"sub": user_id, "username": "dummy", "token_type": "access"}
        raise Exception("Invalid token")

    def refresh_access_token(self, refresh_token):
        """Refresh an access token."""
        if refresh_token.startswith("refresh_"):
            user_id = refresh_token.split("_", 1)[1]
            return f"access_{user_id}"
        raise AuthenticationError("Invalid refresh token")


# Fixture to create a UserManager instance with fake dependencies
@pytest.fixture
def user_manager():
    """Create a UserManager with fake dependencies."""
    db = FakeUserDatabase()
    jwt = FakeJWTManager()
    return UserManager(db, jwt)


# Fixture for sample user data
@pytest.fixture
def sample_user_data():
    """Return sample user data for testing."""
    return {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "password": "password123",
        "shipping_address": "123 Test St",
    }


# --- Tests for register_user method ---
def test_register_user_success(user_manager, sample_user_data) -> None:
    """Test successful user registration."""
    user = user_manager.register_user(**sample_user_data)
    assert user.username == sample_user_data["username"]
    assert user.email == sample_user_data["email"]
    assert user.token is None


def test_register_user_failure(user_manager, sample_user_data) -> None:
    """Test failure when registering a duplicate user."""
    user_manager.register_user(**sample_user_data)
    with pytest.raises(ValueError, match="User registration failed"):
        user_manager.register_user(**sample_user_data)


# --- Tests for login method with parameterization ---
@pytest.mark.parametrize(
    "login_identifier,password,expected",
    [
        ("testuser", "password123", True),
        ("test@example.com", "password123", True),
        ("wronguser", "password123", False),
        ("testuser", "wrongpass", False),
    ],
)
def test_login(
    user_manager, sample_user_data, login_identifier, password, expected
) -> None:
    """Test user login with various credentials."""
    user_manager.register_user(**sample_user_data)
    if expected:
        user, tokens = user_manager.login(login_identifier, password)
        assert user.username == sample_user_data["username"]
        assert "access_token" in tokens and "refresh_token" in tokens
    else:
        with pytest.raises(AuthenticationError):
            user_manager.login(login_identifier, password)


# --- Tests for authenticate_with_token method ---
def test_authenticate_with_token_success(user_manager, sample_user_data) -> None:
    """Test successful authentication with token."""
    user_manager.register_user(**sample_user_data)
    user, tokens = user_manager.login(
        sample_user_data["username"], sample_user_data["password"]
    )
    token = tokens["access_token"]
    authenticated_user = user_manager.authenticate_with_token(token)
    assert authenticated_user.token == token


def test_authenticate_with_token_failure(user_manager) -> None:
    """Test authentication failure with invalid token."""
    with pytest.raises(AuthenticationError):
        user_manager.authenticate_with_token("invalid_token")


# Test: Payload missing token_type in verify_token
def test_authenticate_with_token_missing_token_type(user_manager, monkeypatch) -> None:
    """Test authentication failure when token payload is missing token_type."""

    def fake_verify_token(token):
        return {"sub": "some_id", "username": "dummy"}  # no token_type provided

    monkeypatch.setattr(user_manager._jwt_manager, "verify_token", fake_verify_token)
    with pytest.raises(AuthenticationError, match="Invalid token"):
        user_manager.authenticate_with_token("access_some_id")


# Test: Wrong token type (not 'access')
def test_authenticate_with_token_wrong_token_type(user_manager, monkeypatch) -> None:
    """Test authentication failure with wrong token type."""

    def fake_verify_token(token):
        return {"sub": "some_id", "username": "dummy", "token_type": "refresh"}

    monkeypatch.setattr(user_manager._jwt_manager, "verify_token", fake_verify_token)
    with pytest.raises(
        AuthenticationError, match="Invalid token type for authentication"
    ):
        user_manager.authenticate_with_token("access_some_id")


# Test: Valid payload but user not found in database
def test_authenticate_with_token_user_not_found(user_manager, monkeypatch) -> None:
    """Test authentication failure when user not found in database."""

    def fake_verify_token(token):
        return {"sub": "nonexistent", "username": "dummy", "token_type": "access"}

    monkeypatch.setattr(user_manager._jwt_manager, "verify_token", fake_verify_token)
    with pytest.raises(AuthenticationError, match="User not found"):
        user_manager.authenticate_with_token("access_nonexistent")


# --- Tests for refresh_access_token method ---
def test_refresh_access_token_success(user_manager, sample_user_data) -> None:
    """Test successful access token refresh."""
    user_manager.register_user(**sample_user_data)
    user, tokens = user_manager.login(
        sample_user_data["username"], sample_user_data["password"]
    )
    new_access = user_manager.refresh_access_token(tokens["refresh_token"])
    assert new_access.startswith("access_")


def test_refresh_access_token_failure(user_manager) -> None:
    """Test access token refresh failure with invalid refresh token."""
    with pytest.raises(AuthenticationError):
        user_manager.refresh_access_token("invalid_refresh")


# --- Tests for logout method ---
def test_logout(user_manager, sample_user_data) -> None:
    """Test user logout."""
    user = user_manager.register_user(**sample_user_data)
    user.token = "sometoken"
    result = user_manager.logout(user)
    assert result is True
    assert user.token is None


# Test logout with None user
def test_logout_with_none(user_manager) -> None:
    """Test logout with None user."""
    result = user_manager.logout(None)
    assert result is False


# --- Tests for update_user method ---
@pytest.mark.parametrize(
    "update_kwargs",
    [
        {"full_name": "New Name"},
        {"email": "new@example.com"},
        {"shipping_address": "456 New St"},
        {"full_name": "New Name", "email": "new@example.com"},
        {},  # No changes – should return True
    ],
)
def test_update_user_success(user_manager, sample_user_data, update_kwargs) -> None:
    """Test successful user updates with various fields."""
    user_manager.register_user(**sample_user_data)
    result = user_manager.update_user(sample_user_data["username"], **update_kwargs)
    assert result is True


def test_update_user_failure(user_manager) -> None:
    """Test user update failure with non-existent user."""
    with pytest.raises(ValueError):
        user_manager.update_user("nonexistent", {"full_name": "New Name"})


# --- Tests for update_password method ---
@pytest.mark.parametrize(
    "current_pwd,new_pwd,expect_success",
    [
        ("password123", "newpassword", True),
        ("wrongpassword", "newpassword", False),
    ],
)
def test_update_password(
    user_manager, sample_user_data, current_pwd, new_pwd, expect_success
) -> None:
    """Test password updates with correct and incorrect current passwords."""
    user_manager.register_user(**sample_user_data)
    if expect_success:
        result = user_manager.update_password(
            sample_user_data["username"], current_pwd, new_pwd
        )
        assert result is True
    else:
        with pytest.raises(AuthenticationError):
            user_manager.update_password(
                sample_user_data["username"], current_pwd, new_pwd
            )


# Test: update_password failure due to update error (e.g., weak new password)
def test_update_password_update_failure(
    user_manager, sample_user_data, monkeypatch
) -> None:
    """Test password update failure due to validation errors."""
    user_manager.register_user(**sample_user_data)

    def fake_update_user(username, updated_data):
        raise ValueError("New password is too weak")

    monkeypatch.setattr(user_manager._user_db, "update_user", fake_update_user)
    with pytest.raises(
        ValueError, match="Password update failed: New password is too weak"
    ):
        user_manager.update_password(
            sample_user_data["username"], "password123", "weakpassword"
        )
