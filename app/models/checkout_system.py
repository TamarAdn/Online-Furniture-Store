import uuid

from app.models.enums import PaymentMethod
from app.models.inventory import Inventory
from app.models.order import Order
from app.models.order_manager import OrderManager
from app.models.shopping_cart import ShoppingCart
from app.models.user import User
from app.utils import AuthenticationError


class CheckoutSystem:
    """
    Handles the checkout process for orders in the furniture eCommerce system.

    This class coordinates validation, payment processing, order creation,
    inventory updates, and cart clearing.
    """

    def __init__(self, inventory: Inventory, order_manager: OrderManager) -> None:
        """
        Initialize a CheckoutSystem with inventory and order management components.

        Args:
            inventory: The inventory system to check and update stock
            order_manager: The system for managing created orders
        """
        self._inventory = inventory
        self._order_manager = order_manager

    def process_checkout(self, user: "User", payment_method: PaymentMethod) -> Order:
        """
        Process a checkout for a user.

        Args:
            user: The user checking out
            payment_method: The method of payment

        Returns:
            The created order object

        Raises:
            AuthenticationError: If the user is not authenticated.
            ValueError: If the user has no shipping address.
            Exception: For an empty cart, inventory issues, or payment failure.
        """
        self._validate_user(user)
        cart = user.shopping_cart
        self._validate_cart(cart)
        self._check_inventory_availability(cart)

        if not self._process_payment(payment_method, cart.get_total()):
            raise Exception("Payment processing failed")

        order = self._create_order(user, cart, payment_method)
        self._update_inventory(cart)
        self._order_manager.save_order(order)
        self._finalize_checkout(cart)

        return order

    def _validate_user(self, user: "User") -> None:
        """
        Validate that the user can proceed with checkout.

        Args:
            user: The user to validate

        Raises:
            AuthenticationError: If the user is not authenticated
            ValueError: If shipping address is missing
        """
        if not user.is_authenticated:
            raise AuthenticationError("You must be logged in to checkout")

        if not user.shipping_address:
            raise ValueError(
                "User must have a registered shipping address to place an order"
            )

    def _validate_cart(self, cart: ShoppingCart) -> None:
        """
        Validate that the cart has items for checkout.

        Args:
            cart: The shopping cart to validate

        Raises:
            Exception: If the cart is empty
        """
        if cart.is_empty():
            raise Exception("Cannot checkout with an empty cart")

    def _check_inventory_availability(self, cart: ShoppingCart) -> None:
        """
        Check that all items in the cart are available in the inventory.

        Args:
            cart: The shopping cart to check

        Raises:
            Exception: If any item is not available in requested quantity
        """
        for furniture, quantity in cart.get_items():
            if not self._inventory.is_available(furniture.id, quantity):
                raise Exception(f"Not enough {furniture.name} in inventory")

    def _process_payment(self, payment_method: PaymentMethod, amount: float) -> bool:
        """
        Process payment for the order.

        Args:
            payment_method: The payment method to use
            amount: The total amount to charge

        Returns:
            True if payment succeeded, False otherwise
        """
        # Mock payment processing – always succeeds in this implementation.
        return True

    def _create_order(
        self, user: "User", cart: ShoppingCart, payment_method: PaymentMethod
    ) -> Order:
        """
        Create a new order from the cart contents.

        Args:
            user: The user placing the order
            cart: The shopping cart with items to order
            payment_method: The payment method used

        Returns:
            A new Order object
        """
        order_id = str(uuid.uuid4())
        shipping_address = user.shipping_address

        if shipping_address is None:
            raise ValueError("Shipping address cannot be None at this point")

        return Order(
            order_id=order_id,
            user_id=user.id,
            items=cart.get_items(),
            total_price=cart.get_total(),
            payment_method=payment_method,
            shipping_address=shipping_address,
        )

    def _update_inventory(self, cart: ShoppingCart) -> None:
        """
        Update inventory quantities after a successful order.

        Args:
            cart: The shopping cart containing the ordered items
        """
        for furniture, quantity in cart.get_items():
            current_quantity = self._inventory.get_quantity(furniture.id)
            self._inventory.update_quantity(furniture.id, current_quantity - quantity)

    def _finalize_checkout(self, cart: ShoppingCart) -> None:
        """
        Complete the checkout process by clearing the cart.

        Args:
            cart: The shopping cart to clear
        """
        cart.clear()
