from typing import Dict, List, Optional

from app.models.furniture import Furniture
from app.models.shopping_cart import ShoppingCart
from app.utils import AuthenticationError


class User:

    """Represents a user entity in the furniture ecommerce system.

    Stores user profile information, maintains authentication state,
    and provides user-specific features including:
    - Profile data access and validation
    - Authentication state tracking
    - Shopping cart management
    - Favorites collection management
    """

    def __init__(
        self,
        user_id: str,
        username: str,
        full_name: str,
        email: str,
        shipping_address: Optional[str] = None,
    ) -> None:
        """
        Initialize a new User instance.

        Args:
            user_id: Unique identifier for the user
            username: Unique username for login
            full_name: User's full name
            email: User's email address
            shipping_address: User's shipping address (optional)
        """
        self._id: str = user_id
        self._username: str = username
        self._full_name: str = full_name
        self._email: str = email
        self._shipping_address: Optional[str] = shipping_address
        self._token: Optional[str] = None
        self._shopping_cart: ShoppingCart = ShoppingCart()
        self._favorites: Dict[str, "Furniture"] = {}

    @property
    def id(self) -> str:
        """Get the user's unique identifier."""
        return self._id

    @property
    def username(self) -> str:
        """Get the user's username."""
        return self._username

    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return self._full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        """Set the user's full name with validation."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Full name must be a non-empty string.")
        if len(value) < 2 or len(value) > 100:
            raise ValueError("Full name must be between 2 and 100 characters.")
        self._full_name = value

    @property
    def email(self) -> str:
        """Get the user's email address."""
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        """Set the user's email address with validation."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Email must be a non-empty string.")
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError("Invalid email format.")
        self._email = value

    @property
    def shipping_address(self) -> Optional[str]:
        """Get the user's shipping address."""
        return self._shipping_address

    @shipping_address.setter
    def shipping_address(self, value: str) -> None:
        """Set the user's shipping address with validation."""
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Address must be a non-empty string.")
        if len(value) < 5 or len(value) > 200:
            raise ValueError("Address must be between 5 and 200 characters.")
        self._shipping_address = value

    @property
    def token(self) -> Optional[str]:
        """Get the user's authentication token."""
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        """Set the user's authentication token."""
        self._token = value

    @property
    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated.

        Returns:
            bool: True if the user has a valid token, False otherwise
        """
        return self._token is not None

    @property
    def shopping_cart(self) -> "ShoppingCart":
        """
        Get the user's shopping cart.

        Using a property maintains encapsulation while providing access to the cart.
        The ShoppingCart class controls its own internal implementation.

        Returns:
            ShoppingCart: The user's shopping cart instance
        """
        return self._shopping_cart

    def add_to_favorites(self, furniture: "Furniture") -> None:
        """
        Add a furniture item to the user's favorites.

        Args:
            furniture: The furniture item to add to favorites

        Raises:
            AuthenticationError: If the user is not authenticated
        """
        if not self.is_authenticated:
            raise AuthenticationError("You must be logged in to add items to favorites")

        self._favorites[furniture.id] = furniture

    def remove_from_favorites(self, furniture_id: str) -> None:
        """
        Remove a furniture item from the user's favorites.

        Args:
            furniture_id: ID of the furniture item to remove

        Raises:
            AuthenticationError: If the user is not authenticated
        """
        if not self.is_authenticated:
            raise AuthenticationError(
                "You must be logged in to remove items from favorites"
            )

        if furniture_id in self._favorites:
            del self._favorites[furniture_id]

    def view_favorites(self) -> Dict[str, "Furniture"]:
        """
        Get the dictionary of user's favorite furniture items.

        Returns:
            Dict: Dictionary of furniture items in favorites
            (key: furniture ID, value: furniture object)

        Raises:
            AuthenticationError: If the user is not authenticated
        """
        if not self.is_authenticated:
            raise AuthenticationError("You must be logged in to view favorites")

        return self._favorites

    def view_cart(self) -> List["Furniture"]:
        """
        View the contents of the user's shopping cart.

        Returns:
            List: List of furniture items in the shopping cart

        Raises:
            AuthenticationError: If the user is not authenticated
        """
        if not self.is_authenticated:
            raise AuthenticationError("You must be logged in to view your cart")

        return self.shopping_cart.get_items()
