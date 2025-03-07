"""Test module for shopping cart functionality."""
import pytest

from app.models.discount_strategy import NoDiscountStrategy
from app.models.furniture import Furniture
from app.models.inventory import Inventory
from app.models.shopping_cart import ShoppingCart


# --- Dummy Classes for Testing ---
class DummyFurniture(Furniture):
    """Dummy furniture class for testing."""

    def __init__(self, fid: str, name: str, final_price: float) -> None:
        """Initialize dummy furniture with basic properties.

        Args:
            fid: Furniture ID
            name: Furniture name
            final_price: Final price of the furniture
        """
        # Set the underlying private attributes instead of the read-only properties.
        object.__setattr__(self, "_id", fid)
        object.__setattr__(self, "_name", name)
        self._final_price = final_price

    def get_final_price(self) -> float:
        """Get the final price of the furniture.

        Returns:
            The final price
        """
        return self._final_price

    def get_specific_attributes(self) -> dict:
        """Get furniture-specific attributes.

        Returns:
            Empty dictionary as this is a dummy implementation
        """
        return {}


class DummyInventory:
    """Dummy inventory for testing shopping cart."""

    def __init__(self, available: bool = True) -> None:
        """Initialize dummy inventory.

        Args:
            available: Whether items should be considered available
        """
        self.available = available

    def is_available(self, fid: str, quantity: int) -> bool:
        """Check if a furniture item is available.

        Args:
            fid: Furniture ID
            quantity: Quantity requested

        Returns:
            Whether the furniture is available in requested quantity
        """
        return self.available


class DummyDiscountStrategy:
    """Dummy discount strategy for testing."""

    def apply_discount(self, price: float) -> float:
        """Apply a 20% discount to the price.

        Args:
            price: Original price

        Returns:
            Discounted price (80% of original)
        """
        # For testing, simply return 80% of the price.
        return price * 0.8


# --- Fixtures ---
@pytest.fixture
def dummy_furniture() -> DummyFurniture:
    """Return a dummy furniture instance with id 'F1', name 'Chair', final_price 100."""
    return DummyFurniture("F1", "Chair", 100)


@pytest.fixture
def dummy_inventory_available() -> DummyInventory:
    """Return a dummy inventory that always indicates items are available."""
    return DummyInventory(available=True)


@pytest.fixture
def dummy_inventory_unavailable() -> DummyInventory:
    """Return a dummy inventory that always indicates items are NOT available."""
    return DummyInventory(available=False)


@pytest.fixture
def shopping_cart(dummy_inventory_available: DummyInventory) -> ShoppingCart:
    """Return a ShoppingCart instance using the available dummy inventory."""
    return ShoppingCart(inventory=dummy_inventory_available)


@pytest.fixture
def populated_cart(
    shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture
) -> ShoppingCart:
    """Return a shopping cart with items already added."""
    shopping_cart.add_item(dummy_furniture, 3)
    return shopping_cart


# --- Tests for Discount Strategy Property ---
def test_discount_strategy_default(shopping_cart: ShoppingCart) -> None:
    """Test the default discount strategy of a shopping cart."""
    # The default discount strategy should be an instance of NoDiscountStrategy.
    assert isinstance(shopping_cart.discount_strategy, NoDiscountStrategy)


def test_discount_strategy_setter(shopping_cart: ShoppingCart) -> None:
    """Test setting the discount strategy property."""
    # Setting None should revert to NoDiscountStrategy.
    shopping_cart.discount_strategy = None
    assert isinstance(shopping_cart.discount_strategy, NoDiscountStrategy)

    # Setting a custom strategy.
    dummy_strategy = DummyDiscountStrategy()
    shopping_cart.discount_strategy = dummy_strategy
    assert shopping_cart.discount_strategy == dummy_strategy


# --- Tests for add_item ---
def test_add_item_invalid_type(shopping_cart: ShoppingCart) -> None:
    """Test adding an invalid item type to the cart."""
    with pytest.raises(TypeError, match="Item must be a Furniture object"):
        shopping_cart.add_item("not a furniture", 1)


@pytest.mark.parametrize("invalid_qty", [0, -1])
def test_add_item_invalid_quantity(
    shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture, invalid_qty: int
) -> None:
    """Test adding items with invalid quantities."""
    with pytest.raises(ValueError, match="Quantity must be positive"):
        shopping_cart.add_item(dummy_furniture, invalid_qty)


def test_add_item_not_enough_inventory(dummy_furniture: DummyFurniture) -> None:
    """Test adding items when inventory is insufficient."""
    # Use a dummy inventory that always returns False.
    cart = ShoppingCart(inventory=DummyInventory(available=False))
    with pytest.raises(
        ValueError, match=f"Not enough {dummy_furniture.name} in inventory"
    ):
        cart.add_item(dummy_furniture, 1)


def test_add_item_new_item(
    shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture
) -> None:
    """Test adding a new item to the cart."""
    shopping_cart.add_item(dummy_furniture, 2)
    # The cart's internal _items should have an entry with quantity 2.
    assert dummy_furniture.id in shopping_cart._items
    assert shopping_cart._items[dummy_furniture.id][1] == 2


def test_add_item_existing_item(
    shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture
) -> None:
    """Test adding more quantity of an existing item."""
    shopping_cart.add_item(dummy_furniture, 2)
    shopping_cart.add_item(dummy_furniture, 3)
    # Total quantity should update to 5.
    assert shopping_cart._items[dummy_furniture.id][1] == 5


# --- Test for _get_inventory ---
def test_get_inventory_creates_instance() -> None:
    """Test that _get_inventory creates an Inventory instance when none is provided."""
    # When no inventory is provided, _get_inventory should create one.
    cart = ShoppingCart(inventory=None)
    inv = cart._get_inventory()
    assert isinstance(inv, Inventory)


# --- Tests for remove_item ---
def test_remove_item_complete(
    shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture
) -> None:
    """Test completely removing an item from the cart."""
    shopping_cart.add_item(dummy_furniture, 3)
    result = shopping_cart.remove_item(dummy_furniture.id)
    assert result is True
    assert dummy_furniture.id not in shopping_cart._items


def test_remove_item_partial(
    shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture
) -> None:
    """Test partially removing quantities of an item."""
    shopping_cart.add_item(dummy_furniture, 5)
    # Remove 2 units.
    result = shopping_cart.remove_item(dummy_furniture.id, 2)
    assert result is True
    assert shopping_cart._items[dummy_furniture.id][1] == 3


def test_remove_item_not_in_cart(shopping_cart: ShoppingCart) -> None:
    """Test removing an item that isn't in the cart."""
    result = shopping_cart.remove_item("nonexistent")
    assert result is False


# --- Added missing tests from File 1 ---
def test_remove_item_negative_quantity(
    populated_cart: ShoppingCart, dummy_furniture: DummyFurniture
) -> None:
    """Test that removing a negative quantity raises ValueError."""
    with pytest.raises(ValueError, match="Quantity to remove must be non-negative"):
        populated_cart.remove_item(dummy_furniture.id, -2)


@pytest.mark.parametrize(
    "item_id, quantity, expected_result",
    [("F1", 1, False), ("nonexistent", None, False)],
)
def test_remove_from_empty_cart(
    shopping_cart: ShoppingCart, item_id: str, quantity: int, expected_result: bool
) -> None:
    """Test removing items from an empty cart returns False."""
    result = shopping_cart.remove_item(item_id, quantity)
    assert result is expected_result


# --- Test for get_items (defensive copy) ---
def test_get_items_defensive_copy(
    shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture
) -> None:
    """Test that get_items returns a defensive copy."""
    shopping_cart.add_item(dummy_furniture, 4)
    items_copy = shopping_cart.get_items()
    # Modify the returned copy.
    items_copy[0][1] = 100
    # The internal state should remain unchanged.
    assert shopping_cart._items[dummy_furniture.id][1] == 4


# --- Tests for get_subtotal and get_total ---
def test_get_subtotal(shopping_cart: ShoppingCart) -> None:
    """Test the subtotal calculation of items in cart."""
    # Add two items with known final prices.
    furniture1 = DummyFurniture("F1", "Chair", 100)
    furniture2 = DummyFurniture("F2", "Table", 200)
    shopping_cart.add_item(furniture1, 2)  # subtotal = 2 * 100 = 200
    shopping_cart.add_item(furniture2, 1)  # subtotal = 1 * 200 = 200
    subtotal = shopping_cart.get_subtotal()
    assert subtotal == 400


def test_get_total(shopping_cart: ShoppingCart) -> None:
    """Test the total calculation with and without discount."""
    # Without discount, total equals subtotal.
    furniture = DummyFurniture("F1", "Chair", 100)
    shopping_cart.add_item(furniture, 2)  # subtotal = 200
    total = shopping_cart.get_total()
    assert total == 200

    # Set a dummy discount strategy that returns 80% of the price.
    dummy_strategy = DummyDiscountStrategy()
    shopping_cart.discount_strategy = dummy_strategy
    total_discounted = shopping_cart.get_total()
    # 80% of 200 should be 160.
    assert total_discounted == 160


@pytest.mark.parametrize("cart_fixture, expected_value", [("shopping_cart", 0)])
def test_get_subtotal_empty_cart(
    request, cart_fixture: str, expected_value: int
) -> None:
    """Test that empty cart returns zero subtotal."""
    cart = request.getfixturevalue(cart_fixture)
    assert cart.is_empty()  # confirm cart is empty
    assert cart.get_subtotal() == expected_value


@pytest.mark.parametrize("cart_fixture, expected_value", [("shopping_cart", 0)])
def test_get_total_empty_cart(request, cart_fixture: str, expected_value: int) -> None:
    """Test that empty cart returns zero total."""
    cart = request.getfixturevalue(cart_fixture)
    assert cart.is_empty()  # confirm cart is empty
    assert cart.get_total() == expected_value


# --- Tests for clear, is_empty, and __len__ ---
def test_clear_and_is_empty(
    shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture
) -> None:
    """Test clearing the cart and checking if it's empty."""
    shopping_cart.add_item(dummy_furniture, 3)
    assert not shopping_cart.is_empty()
    shopping_cart.clear()
    assert shopping_cart.is_empty()


def test_len(shopping_cart: ShoppingCart, dummy_furniture: DummyFurniture) -> None:
    """Test the length operator for cart items."""
    shopping_cart.add_item(dummy_furniture, 2)
    # Add a second distinct item.
    furniture2 = DummyFurniture("F2", "Table", 150)
    shopping_cart.add_item(furniture2, 3)
    # Total length should equal 2 + 3 = 5.
    assert len(shopping_cart) == 5
