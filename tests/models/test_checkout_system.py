import pytest

from app.models.checkout_system import CheckoutSystem
from app.models.enums import PaymentMethod
from app.models.order import Order


# --- Dummy Classes for Testing ---
class FakeFurniture:
    """Mock furniture class for testing checkout functionality."""

    def __init__(self, fid: str, name: str, final_price: float) -> None:
        """Initialize fake furniture with ID, name, and price.

        Args:
            fid: Furniture ID
            name: Furniture name
            final_price: Price of the furniture
        """
        self.id = fid
        self.name = name
        self._final_price = final_price

    def get_final_price(self) -> float:
        """Get the final price of the furniture.

        Returns:
            The final price
        """
        return self._final_price


class FakeShoppingCart:
    """Mock shopping cart for testing checkout functionality."""

    def __init__(self, items: list, total: float) -> None:
        """Initialize fake shopping cart with items and total.

        Args:
            items: List of (furniture, quantity) tuples
            total: Total cost of items in cart
        """
        self._items = items  # items: list of (furniture, quantity) tuples
        self._total = total
        self.cleared = False

    def is_empty(self) -> bool:
        """Check if cart is empty.

        Returns:
            True if cart has no items
        """
        return len(self._items) == 0

    def get_items(self) -> list:
        """Get items in the cart.

        Returns:
            List of (furniture, quantity) tuples
        """
        return self._items

    def get_total(self) -> float:
        """Get total cost of items in cart.

        Returns:
            Total cost
        """
        return self._total

    def clear(self) -> None:
        """Clear all items from the cart."""
        self.cleared = True
        self._items = []


class FakeUser:
    """Mock user class for testing checkout functionality."""

    def __init__(
        self,
        is_authenticated: bool,
        shipping_address: str,
        user_id: str,
        shopping_cart: FakeShoppingCart,
    ) -> None:
        """Initialize fake user with authentication status and details.

        Args:
            is_authenticated: Whether the user is logged in
            shipping_address: User's shipping address
            user_id: User ID
            shopping_cart: User's shopping cart
        """
        self.is_authenticated = is_authenticated
        self.shipping_address = shipping_address
        self.id = user_id
        self.shopping_cart = shopping_cart


class FakeInventory:
    """Mock inventory class for testing checkout functionality."""

    def __init__(self, available: bool = True, quantity: int = 10) -> None:
        """Initialize fake inventory with availability status.

        Args:
            available: Whether items are available
            quantity: Default quantity of items
        """
        self.available = available
        self.quantity = quantity
        self.updated = False

    def is_available(self, fid: str, quantity: int) -> bool:
        """Check if inventory has enough of an item.

        Args:
            fid: Furniture ID
            quantity: Quantity requested

        Returns:
            True if enough inventory available
        """
        return self.available and (self.quantity >= quantity)

    def get_quantity(self, fid: str) -> int:
        """Get quantity of an item in inventory.

        Args:
            fid: Furniture ID

        Returns:
            Quantity available
        """
        return self.quantity

    def update_quantity(self, fid: str, new_quantity: int) -> None:
        """Update quantity of an item in inventory.

        Args:
            fid: Furniture ID
            new_quantity: New quantity value
        """
        self.updated = True
        self.quantity = new_quantity


class FakeOrderManager:
    """Mock order manager for testing checkout functionality."""

    def __init__(self) -> None:
        """Initialize fake order manager."""
        self.saved_orders = []

    def save_order(self, order: Order) -> None:
        """Save an order.

        Args:
            order: Order to save
        """
        self.saved_orders.append(order)


# -----------------------------
# Parameterized tests for checkout failure scenarios.
# -----------------------------
@pytest.mark.parametrize(
    "is_authenticated, shipping_address, cart_items, inventory_available, "
    "payment_success, expected_error",
    [
        # 1. User not authenticated.
        (
            False,
            "123 Main St",
            [(FakeFurniture("F1", "Chair", 100), 2)],
            True,
            True,
            "You must be logged in to checkout",
        ),
        # 2. Empty cart.
        (True, "123 Main St", [], True, True, "Cannot checkout with an empty cart"),
        # 3. Missing shipping address.
        (
            True,
            "",
            [(FakeFurniture("F1", "Chair", 100), 2)],
            True,
            True,
            "User must have a registered shipping address",
        ),
        # 4. Inventory not available.
        (
            True,
            "123 Main St",
            [(FakeFurniture("F1", "Chair", 100), 2)],
            False,
            True,
            "Not enough Chair in inventory",
        ),
        # 5. Payment processing failure.
        (
            True,
            "123 Main St",
            [(FakeFurniture("F1", "Chair", 100), 2)],
            True,
            False,
            "Payment processing failed",
        ),
    ],
)
def test_process_checkout_fail(
    is_authenticated: bool,
    shipping_address: str,
    cart_items: list,
    inventory_available: bool,
    payment_success: bool,
    expected_error: str,
) -> None:
    """Test various checkout failure scenarios."""
    inventory = FakeInventory(available=inventory_available, quantity=10)
    order_manager = FakeOrderManager()
    checkout = CheckoutSystem(inventory, order_manager)
    total = sum(f.get_final_price() * qty for f, qty in cart_items)
    cart = FakeShoppingCart(cart_items, total=total)
    user = FakeUser(is_authenticated, shipping_address, "U1", cart)

    # If we want to simulate payment failure, override _process_payment.
    if not payment_success:
        checkout._process_payment = lambda pm, amt: False

    with pytest.raises(Exception, match=expected_error):
        checkout.process_checkout(user, PaymentMethod.CREDIT_CARD)


# -----------------------------
# Test for successful checkout.
# -----------------------------
def test_process_checkout_success() -> None:
    """Test successful checkout process."""
    inventory = FakeInventory(available=True, quantity=10)
    order_manager = FakeOrderManager()
    checkout = CheckoutSystem(inventory, order_manager)

    furniture = FakeFurniture("F1", "Chair", 100)
    cart_items = [(furniture, 2)]
    cart = FakeShoppingCart(cart_items, total=200)
    user = FakeUser(
        is_authenticated=True,
        shipping_address="123 Main St",
        user_id="U1",
        shopping_cart=cart,
    )

    order = checkout.process_checkout(user, PaymentMethod.CREDIT_CARD)

    # Verify order properties.
    assert isinstance(order, Order)
    assert order.user_id == "U1"
    assert order.total_price == 200
    assert order.payment_method == PaymentMethod.CREDIT_CARD
    assert order.shipping_address == "123 Main St"

    # Verify that order_manager saved the order.
    assert len(order_manager.saved_orders) == 1

    # Verify that inventory was updated.
    assert inventory.updated is True

    # Verify that the cart was cleared.
    assert cart.is_empty() is True
    assert cart.cleared is True
