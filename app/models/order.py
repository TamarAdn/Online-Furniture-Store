import datetime
from dataclasses import dataclass, field
from typing import Any, List, Tuple

from app.models.enums import PaymentMethod


@dataclass
class Order:
    """
    Represents an order in the furniture e-commerce system.
    """

    order_id: str
    user_id: str
    items: List[Tuple[Any, int]]
    total_price: float
    payment_method: PaymentMethod
    shipping_address: str
    date: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __post_init__(self) -> None:
        """
        Validate order attributes after initialization.

        Raises:
            TypeError: When an attribute has an incorrect type
            ValueError: When an attribute has an invalid value
        """
        # ensure basic structural validation
        if not isinstance(self.items, list):
            raise TypeError("Items must be a list")
        # ensure every item is valid
        for item in self.items:
            if not isinstance(item, (list, tuple)) or len(item) != 2:
                raise TypeError(
                    "Each item must be a (furniture, quantity) tuple or list"
                )

        # ensure order_id is a string
        if not isinstance(self.order_id, str):
            raise TypeError("order_id must be a string")

        # ensure user_id is a string
        if not isinstance(self.user_id, str):
            raise TypeError("user_id must be a string")

        # ensure items list is not empty
        if not self.items:
            raise ValueError("Order must contain at least one item")

        # ensure payment method is from ENUM
        if not isinstance(self.payment_method, PaymentMethod):
            raise TypeError("payment_method must be a valid PaymentMethod enum")

        # ensure total price is non negative
        if not isinstance(self.total_price, (int, float)) or self.total_price < 0:
            raise ValueError("total_price must be a non-negative number")

    @property
    def id(self) -> str:
        """
        Get the order ID.

        Returns:
            The order's unique identifier
        """
        return self.order_id

    def __str__(self) -> str:
        """
        Get a string representation of the order.

        Returns:
            A string showing the order ID and total price
        """
        return f"Order #{self.order_id} - ${self.total_price:.2f}"
