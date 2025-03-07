import pytest

from app.models.user import User
from app.utils import AuthenticationError


# Fake implementations for dependent classes
class FakeShoppingCart:
    """Fake shopping cart implementation for testing."""

    def __init__(self):
        """Initialize with empty items list."""
        self.items = []

    def get_items(self):
        """Get the items in the cart."""
        return self.items

    def add_item(self, item):
        """Add an item to the cart."""
        self.items.append(item)


class FakeFurniture:
    """Fake furniture implementation for testing."""

    def __init__(self, fid, name="Chair"):
        """Initialize with ID and name."""
        self.id = fid
        self.name = name


# --- Helper fixture to create a default User instance ---
@pytest.fixture
def sample_user():
    """Create a sample user with valid data."""
    # Create a sample user with valid data
    user = User("user-123", "testuser", "Test User", "test@example.com", "123 Test St")
    # By default the user is not authenticated (_token is None)
    return user


# --- Tests for property getters and setters ---
def test_user_properties(sample_user) -> None:
    """Test basic user properties and getters."""
    # Test getters
    assert sample_user.id == "user-123"
    assert sample_user.username == "testuser"
    assert sample_user.full_name == "Test User"
    assert sample_user.email == "test@example.com"
    assert sample_user.shipping_address == "123 Test St"
    # By default, token is None and not authenticated
    assert sample_user.token is None
    assert sample_user.is_authenticated is False
    # Shopping cart should be an instance with a list of items
    assert isinstance(sample_user.shopping_cart.get_items(), list)


def test_full_name_setter_valid(sample_user) -> None:
    """Test setting a valid full name."""
    sample_user.full_name = "New Name"
    assert sample_user.full_name == "New Name"


@pytest.mark.parametrize("invalid_name", ["", " ", "A", "a" * 101])
def test_full_name_setter_invalid(sample_user, invalid_name) -> None:
    """Test setting invalid full names."""
    with pytest.raises(ValueError, match="Full name"):
        sample_user.full_name = invalid_name


def test_email_setter_valid(sample_user) -> None:
    """Test setting a valid email address."""
    sample_user.email = "new@example.com"
    assert sample_user.email == "new@example.com"


# Using parameterization with expected error substring for invalid email values
@pytest.mark.parametrize(
    "invalid_email,expected_error",
    [
        ("", "Email must be a non-empty string."),
        ("noatsign", "Invalid email format."),
        ("user@domain", "Invalid email format."),
        ("userdomain.com", "Invalid email format."),
    ],
)
def test_email_setter_invalid(sample_user, invalid_email, expected_error) -> None:
    """Test setting invalid email addresses."""
    with pytest.raises(ValueError, match=expected_error):
        sample_user.email = invalid_email


def test_shipping_address_setter_valid(sample_user) -> None:
    """Test setting a valid shipping address."""
    sample_user.shipping_address = "456 New Ave"
    assert sample_user.shipping_address == "456 New Ave"


@pytest.mark.parametrize("invalid_address", ["", " ", "1234", "A" * 201])
def test_shipping_address_setter_invalid(sample_user, invalid_address) -> None:
    """Test setting invalid shipping addresses."""
    with pytest.raises(ValueError, match="Address"):
        sample_user.shipping_address = invalid_address


def test_token_setter_and_is_authenticated(sample_user) -> None:
    """Test token setter and authentication status."""
    # Initially not authenticated
    assert sample_user.is_authenticated is False
    sample_user.token = "sometoken"
    assert sample_user.token == "sometoken"
    assert sample_user.is_authenticated is True


# --- Tests for favorites functionality ---
def test_add_to_favorites_success(sample_user) -> None:
    """Test successfully adding an item to favorites."""
    # Set token to simulate authenticated user
    sample_user.token = "validtoken"
    furniture = FakeFurniture("furn-1", "Sofa")
    sample_user.add_to_favorites(furniture)
    # Favorites should now include the furniture by its id
    favorites = sample_user.view_favorites()
    assert "furn-1" in favorites
    assert favorites["furn-1"].name == "Sofa"


def test_add_to_favorites_unauthenticated(sample_user) -> None:
    """Test adding to favorites when unauthenticated."""
    # User without token is not authenticated
    furniture = FakeFurniture("furn-2", "Table")
    with pytest.raises(AuthenticationError, match="logged in"):
        sample_user.add_to_favorites(furniture)


def test_remove_from_favorites_success(sample_user) -> None:
    """Test successfully removing an item from favorites."""
    sample_user.token = "validtoken"
    furniture = FakeFurniture("furn-3", "Lamp")
    # Add then remove the item
    sample_user.add_to_favorites(furniture)
    sample_user.remove_from_favorites("furn-3")
    favorites = sample_user.view_favorites()
    assert "furn-3" not in favorites


def test_remove_from_favorites_unauthenticated(sample_user) -> None:
    """Test removing from favorites when unauthenticated."""
    with pytest.raises(AuthenticationError, match="logged in"):
        sample_user.remove_from_favorites("furn-4")


def test_view_favorites_authenticated(sample_user) -> None:
    """Test viewing favorites when authenticated."""
    sample_user.token = "validtoken"
    furniture = FakeFurniture("furn-5", "Desk")
    sample_user.add_to_favorites(furniture)
    favorites = sample_user.view_favorites()
    assert isinstance(favorites, dict)
    assert "furn-5" in favorites


def test_view_favorites_unauthenticated(sample_user) -> None:
    """Test viewing favorites when unauthenticated."""
    with pytest.raises(AuthenticationError, match="logged in"):
        sample_user.view_favorites()


# --- Tests for shopping cart functionality ---
def test_view_cart_authenticated(sample_user) -> None:
    """Test viewing cart when authenticated."""
    sample_user.token = "validtoken"
    # Replace the shopping cart with a fake one to simulate adding items
    fake_cart = FakeShoppingCart()
    item1 = FakeFurniture("furn-6", "Chair")
    item2 = FakeFurniture("furn-7", "Table")
    fake_cart.add_item(item1)
    fake_cart.add_item(item2)
    sample_user._shopping_cart = fake_cart  # override the cart instance
    cart_items = sample_user.view_cart()
    assert isinstance(cart_items, list)
    assert len(cart_items) == 2
    assert cart_items[0].id == "furn-6"
    assert cart_items[1].id == "furn-7"


def test_view_cart_unauthenticated(sample_user) -> None:
    """Test viewing cart when unauthenticated."""
    with pytest.raises(AuthenticationError, match="logged in"):
        sample_user.view_cart()


# --- Additional test to check that shopping_cart property returns the same object ---
def test_shopping_cart_property(sample_user) -> None:
    """Test that shopping_cart property returns the same instance."""
    cart1 = sample_user.shopping_cart
    cart2 = sample_user.shopping_cart
    # Ensure that the shopping_cart property always returns the same instance
    assert cart1 is cart2
